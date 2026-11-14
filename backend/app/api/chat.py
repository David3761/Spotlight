"""Routes for the assistant conversations."""

from fastapi import APIRouter

from app.api.fixes import ContractErrorRoute, get_error_response
from app.assistant import agent, store
from app.assistant.schemas import (
    ActionRequest,
    ActionResult,
    Conversation,
    ConversationList,
    CreateConversationRequest,
    CreateConversationResponse,
    PostMessageRequest,
    PostMessageResponse,
)

router = APIRouter(route_class=ContractErrorRoute)


def get_not_found_response():
    """Returns the 404 response for a conversation, action or option that does not exist."""
    return get_error_response(404, "conversation_not_found", "Nu am găsit conversația sau acțiunea asta.")


@router.get("/api/scans/{scan_id}/conversations", response_model=ConversationList)
def list_conversations(scan_id: str):
    """Returns the scan's conversations, newest first."""
    return ConversationList(conversations=store.get_summaries(scan_id))


@router.post("/api/scans/{scan_id}/conversations", response_model=CreateConversationResponse)
def create_conversation(scan_id: str, request: CreateConversationRequest):
    """Creates a conversation, optionally with a transcript, and returns its id."""
    cid = store.create_conversation(
        scan_id, request.kind, request.chapter_id, request.title, request.messages or []
    )
    return CreateConversationResponse(cid=cid)


@router.get("/api/conversations/{cid}", response_model=Conversation)
def read_conversation(cid: str):
    """Returns the conversation with its messages."""
    conversation = store.get_conversation(cid)
    if conversation is None:
        return get_not_found_response()
    return conversation


@router.post("/api/conversations/{cid}/messages", response_model=PostMessageResponse)
async def post_message(cid: str, request: PostMessageRequest):
    """Sends the owner's message to the assistant and returns its reply."""
    reply = await agent.send_message(cid, request.text)
    if reply is None:
        return get_not_found_response()
    return PostMessageResponse(reply=reply)


@router.post("/api/conversations/{cid}/actions/{action_id}", response_model=ActionResult)
def post_action(cid: str, action_id: str, request: ActionRequest):
    """Confirms, declines or undoes a proposed action."""
    result = agent.apply_action(cid, action_id, request.option_id)
    if result is None:
        return get_not_found_response()
    return result
