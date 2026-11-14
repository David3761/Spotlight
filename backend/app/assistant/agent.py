"""Runs the assistant: a Gemini function-calling loop over the report, plus the message and action flows."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from google.genai import types

from app.assistant import store
from app.assistant.schemas import (
    ActionOption,
    ActionResult,
    Message,
    ProposedAction,
    ProposedItem,
)
from app.fixes.generate import get_generated_text, get_open_problems
from app.fixes.schemas import Tone
from app.llm.client import PROMPTS_DIR, get_client, get_model
from app.models import Problem, Report
from app.services.resolution import load_report, mark_resolved, unmark_resolved

MAX_ROUNDS = 4
"""The most model calls one owner message may trigger."""

FALLBACK_REPLY = "Nu am reușit să răspund acum. Poți încerca din nou?"
"""The reply when the model gives no text."""

DECLINED_TEXT = "Bine! Spune-mi oricând și le marchez. Le verificăm oricum la următoarea analiză."
"""The follow-up when the owner declines to mark the problems."""

FOLLOWUP_CHIPS = ["Da, hai", "Mai târziu"]
"""The quick replies under the follow-up that suggests the next step."""

TONES: list[Tone] = ["prietenos", "profesionist", "scurt"]
"""The tones the assistant may ask for."""

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_report",
                description="Returns the current scores and the open problems with their check_id.",
            ),
            types.FunctionDeclaration(
                name="propose_mark_resolved",
                description=(
                    "Proposes marking open problems as solved. The owner confirms in the app; "
                    "nothing changes until then."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "check_ids": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="The check_id of every open problem the owner says they fixed.",
                        )
                    },
                    required=["check_ids"],
                ),
            ),
            types.FunctionDeclaration(
                name="generate_fix_text",
                description="Writes the text that fixes an open problem, such as the Instagram bio.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "check_id": types.Schema(type=types.Type.STRING),
                        "tone": types.Schema(type=types.Type.STRING, enum=list(TONES)),
                    },
                    required=["check_id", "tone"],
                ),
            ),
            types.FunctionDeclaration(
                name="what_next",
                description="Returns the open problem with the highest impact on the overall score.",
            ),
        ]
    )
]
"""The four functions the model may call."""

TEXT_ONLY = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(mode=types.FunctionCallingConfigMode.NONE)
)
"""The tool config of the last round, which must answer in text instead of calling more functions."""


async def send_message(cid: str, text: str) -> Message | None:
    """Stores the owner's message, runs the agent and returns its reply, or `None` for an unknown conversation."""
    conversation = store.get_conversation(cid)
    if conversation is None:
        return None
    user_message = Message(
        id=uuid4().hex, role="user", text=text, created_at=datetime.now(UTC)
    )
    reply = await get_reply(conversation.scan_id, conversation.messages, text)
    store.append_messages(cid, [user_message, reply])
    return reply


async def get_reply(scan_id: str, history: list[Message], text: str) -> Message:
    """Returns the assistant's reply to the owner's text, calling the model at most `MAX_ROUNDS` times."""
    contents = [
        types.Content(
            role="user" if message.role == "user" else "model",
            parts=[types.Part.from_text(text=message.text)],
        )
        for message in history
        if message.text
    ]
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=text)]))
    config = types.GenerateContentConfig(
        system_instruction=(PROMPTS_DIR / "assistant_system.md").read_text(encoding="utf-8"),
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    client = get_client()
    model = get_model("smart")
    proposed_actions: list[ProposedAction] = []
    reply_text = None

    for round_number in range(1, MAX_ROUNDS + 1):
        if round_number == MAX_ROUNDS:
            config = config.model_copy(update={"tool_config": TEXT_ONLY})
        response = await client.aio.models.generate_content(
            model=model, contents=contents, config=config
        )
        function_calls = response.function_calls
        if not function_calls:
            reply_text = response.text
            break
        if round_number == MAX_ROUNDS:
            break
        contents.append(response.candidates[0].content)
        response_parts = []
        for call in function_calls:
            result = await run_function(scan_id, call.name, call.args or {}, proposed_actions)
            response_parts.append(
                types.Part.from_function_response(name=call.name, response=result)
            )
        contents.append(types.Content(role="user", parts=response_parts))

    return Message(
        id=uuid4().hex,
        role="assistant",
        text=reply_text or FALLBACK_REPLY,
        created_at=datetime.now(UTC),
        action=proposed_actions[-1] if proposed_actions else None,
    )


async def run_function(
    scan_id: str, name: str, args: dict[str, Any], proposed_actions: list[ProposedAction]
) -> dict[str, Any]:
    """Returns the result of one function the model called; a created action is added to `proposed_actions`."""
    report = load_report(scan_id)
    if name == "get_report":
        return {
            "overall": report.overall,
            "summary": report.summary_ro,
            "chapters": [
                {"id": chapter.id, "name": chapter.name_ro, "score": chapter.score}
                for chapter in report.chapters
            ],
            "open_problems": [
                {
                    "check_id": problem.check_id,
                    "chapter": problem.chapter_name_ro,
                    "title": problem.title_ro,
                    "points": problem.points,
                }
                for problem in get_open_problems(report)
            ],
        }
    if name == "propose_mark_resolved":
        action, left_out = get_proposed_action(report, args.get("check_ids") or [])
        if action is None:
            return {"error": "Niciun check_id nu e o problemă deschisă. Apelează get_report."}
        proposed_actions.append(action)
        result: dict[str, Any] = {"status": "proposed", "items": [item.title_ro for item in action.items]}
        if left_out:
            result["not_included"] = left_out
            result["note"] = "O propunere cuprinde un singur capitol. Propune-le pe celelalte după ce proprietarul răspunde."
        return result
    if name == "generate_fix_text":
        tone = args.get("tone")
        generated = await get_generated_text(
            scan_id, str(args.get("check_id")), tone if tone in TONES else "prietenos", 0
        )
        if generated is None:
            return {"error": "Nu e o problemă deschisă care se rezolvă cu un text."}
        return {"text": generated.text, "included": generated.included_ro}
    if name == "what_next":
        problem = get_next_problem(report)
        if problem is None:
            return {"error": "Nu mai sunt probleme deschise."}
        return {"check_id": problem.check_id, "title": problem.title_ro, "why": problem.why_ro}
    return {"error": f"Funcție necunoscută: {name}"}


def get_proposed_action(report: Report, check_ids: list[str]) -> tuple[ProposedAction | None, list[str]]:
    """Returns a pending action for the open problems among the ids that share the first one's chapter, and the open ids left out."""
    open_problems = {problem.check_id: problem for problem in get_open_problems(report)}
    candidates = [
        open_problems[check_id] for check_id in dict.fromkeys(check_ids) if check_id in open_problems
    ]
    if not candidates:
        return None, []
    chapter_id = candidates[0].chapter_id
    problems = [problem for problem in candidates if problem.chapter_id == chapter_id]
    left_out = [problem.check_id for problem in candidates if problem.chapter_id != chapter_id]
    options = [
        ActionOption(
            id="all",
            label_ro="Da, marchează-le" if len(problems) > 1 else "Da, marchează-l",
            check_ids=[problem.check_id for problem in problems],
        )
    ]
    if len(problems) > 1:
        options += [
            ActionOption(
                id=problem.check_id,
                label_ro=f"Doar: {problem.title_ro}",
                check_ids=[problem.check_id],
            )
            for problem in problems
        ]
    options.append(ActionOption(id="no", label_ro="Nu încă", check_ids=[]))
    action = ProposedAction(
        action_id=uuid4().hex,
        items=[
            ProposedItem(
                check_id=problem.check_id, title_ro=problem.title_ro, points=problem.points
            )
            for problem in problems
        ],
        options=options,
    )
    return action, left_out


def get_next_problem(report: Report) -> Problem | None:
    """Returns the open problem with the highest impact, or `None` when nothing is open."""
    return max(get_open_problems(report), key=lambda problem: problem.impact, default=None)


def apply_action(cid: str, action_id: str, option_id: str) -> ActionResult | None:
    """Confirms, declines or undoes a proposed action; returns `None` for an unknown conversation, action or option."""
    conversation = store.get_conversation(cid)
    action = store.get_action(cid, action_id)
    if conversation is None or action is None:
        return None

    if option_id == "undo":
        if action.status != "confirmed":
            return ActionResult(action=action, score=None, followup=None)
        score = unmark_resolved(conversation.scan_id, action.confirmed_check_ids)
        action.status = "undone"
        store.update_action(cid, action)
        return ActionResult(action=action, score=score, followup=None)

    option = next((candidate for candidate in action.options if candidate.id == option_id), None)
    if option is None:
        return None
    if action.status not in ("pending", "undone"):
        return ActionResult(action=action, score=None, followup=None)

    if not option.check_ids:
        action.status = "declined"
        followup = get_followup(DECLINED_TEXT, [])
        store.update_action(cid, action)
        store.append_messages(cid, [followup])
        return ActionResult(action=action, score=None, followup=followup)

    report_before = load_report(conversation.scan_id)
    open_ids = {problem.check_id for problem in get_open_problems(report_before)}
    still_open = [check_id for check_id in option.check_ids if check_id in open_ids]
    action.status = "confirmed"
    action.confirmed_check_ids = option.check_ids
    if not still_open:
        store.update_action(cid, action)
        return ActionResult(action=action, score=None, followup=None)
    score = mark_resolved(conversation.scan_id, still_open)
    chapter_before = next(
        (chapter.score for chapter in report_before.chapters if chapter.id == score.chapter_id),
        None,
    )
    chapter_name = next(
        chapter.name_ro for chapter in score.report.chapters if chapter.id == score.chapter_id
    )
    next_problem = get_next_problem(score.report)
    followup = get_followup(
        get_confirmed_text(
            chapter_name,
            chapter_before,
            score.chapter_score,
            report_before.overall,
            score.overall,
            next_problem,
        ),
        FOLLOWUP_CHIPS if next_problem else [],
    )
    store.update_action(cid, action, chapter_id=score.chapter_id)
    store.append_messages(cid, [followup])
    return ActionResult(action=action, score=score, followup=followup)


def get_confirmed_text(
    chapter_name: str,
    chapter_before: int | None,
    chapter_after: int,
    overall_before: int,
    overall_after: int,
    next_problem: Problem | None,
) -> str:
    """Returns the follow-up text that reports the new scores and suggests the next step."""
    chapter_part = (
        f"{chapter_name} a urcat de la {chapter_before} la {chapter_after}"
        if chapter_before is not None
        else f"{chapter_name} are acum {chapter_after}"
    )
    text = f"{chapter_part}, iar scorul general de la {overall_before} la {overall_after}."
    if next_problem is None:
        return f"{text} Nu mai ai alte probleme deschise."
    return f"{text} Cel mai rapid pas de aici: {next_problem.title_ro.rstrip('.')}. Îl facem acum?"


def get_followup(text: str, chips: list[str]) -> Message:
    """Returns an assistant message with the given text and quick replies."""
    return Message(
        id=uuid4().hex,
        role="assistant",
        text=text,
        created_at=datetime.now(UTC),
        chips=chips,
    )
