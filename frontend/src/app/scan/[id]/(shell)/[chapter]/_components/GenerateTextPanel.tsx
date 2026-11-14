import { buttonVariant, chipVariant } from "@/components/button-styles";
import { ErrorState } from "@/components/ErrorState";
import { Icon, iconPath } from "@/components/Icon";
import type { Problem, Tone } from "@/lib/types";
import { useCopy } from "../_hooks/use-copy";
import { useGeneratedText } from "../_hooks/use-generated-text";
import { screenIconPath } from "./icons";
import { LoadingBlock } from "./LoadingBlock";
import { PanelBody, PanelFooter, ResolveButton } from "./PanelParts";

/** The tones the owner can pick, in display order. */
const tones: { id: Tone; label: string }[] = [
  { id: "prietenos", label: "Prietenos" },
  { id: "profesionist", label: "Profesionist" },
  { id: "scurt", label: "Scurt" },
];

/** The start of a deep-link label that tells the owner a copy comes first. */
const COPY_AND_OPEN_PREFIX = "Copiază și deschide ";

/** Returns the label shown right after copying, naming the place that opens when the deep-link label does. */
function getCopiedLabel(deepLinkLabel: string | null): string {
  if (deepLinkLabel?.startsWith(COPY_AND_OPEN_PREFIX)) {
    return `Copiat! Deschidem ${deepLinkLabel.slice(COPY_AND_OPEN_PREFIX.length)}…`;
  }
  return "Copiat!";
}

/** A component that writes a text for the owner to edit, copy and paste where `where_ro` says. */
export function GenerateTextPanel({
  scanId,
  problem,
  onResolve,
}: {
  scanId: string;
  problem: Problem;
  onResolve: () => void;
}) {
  const { fix } = problem;
  const { tone, state, text, setText, pickTone, regenerate, retry } = useGeneratedText(scanId, problem.check_id);
  const { isCopied, copy } = useCopy();
  const maxChars = fix.max_chars;
  const isOverLimit = maxChars !== null && text.length > maxChars;

  /** Copies the text, then opens the place where it goes in a new tab. */
  const handleCopyAndOpen = () => {
    void copy(text);
    if (fix.deep_link) {
      window.open(fix.deep_link, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <>
      <PanelBody>
        <p className="rounded-2xl bg-page px-4 py-3.5 text-[13px] leading-normal text-subtle lg:text-sm lg:leading-[1.55]">
          {problem.why_ro}
        </p>

        <div className="flex flex-col gap-2 lg:gap-2.5">
          <label htmlFor="fix-text" className="text-sm font-bold">
            Descrierea ta
          </label>
          {state.status === "loading" && <LoadingBlock label="Scriem descrierea…" />}
          {state.status === "error" && <ErrorState error={state.error} onRetry={retry} />}
          {state.status === "ready" && (
            <>
              <textarea
                id="fix-text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={5}
                aria-describedby="fix-text-count"
                className="min-h-39 w-full resize-y rounded-[18px] border-2 border-accent-outline bg-surface px-4 py-3.5 text-[15px] leading-normal text-ink outline-none focus:border-accent lg:px-4.5 lg:py-4 lg:text-base lg:leading-[1.55]"
              />
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                {state.result.included_ro.length > 0 && (
                  <span className="text-[13px] text-muted">Am inclus: {state.result.included_ro.join(", ")}</span>
                )}
                <span
                  id="fix-text-count"
                  className={`ms-auto text-[13px] font-bold tabular-nums ${isOverLimit ? "text-low-text" : "text-subtle"}`}
                >
                  {maxChars === null ? text.length : `${text.length} / ${maxChars}`}
                </span>
              </div>
            </>
          )}
        </div>

        <div className="flex flex-col gap-2.5">
          <span id="tone-label" className="hidden text-sm font-bold lg:block">
            Ton
          </span>
          <div role="group" aria-labelledby="tone-label" className="flex flex-wrap items-center gap-2">
            {tones.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={item.id === tone}
                onClick={() => pickTone(item.id)}
                className={`${item.id === tone ? chipVariant.pressed : chipVariant.idle} h-11 flex-1 px-4.5 text-sm lg:flex-none`}
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              onClick={regenerate}
              className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full px-4 text-sm font-bold text-accent-hover lg:ms-auto lg:w-auto lg:bg-fill lg:text-body"
            >
              <Icon path={iconPath.refresh} size={17} />
              Generează din nou
            </button>
          </div>
        </div>

        {fix.where_ro && (
          <div className="flex items-start gap-3 text-[13px] leading-normal text-subtle">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-[9px] bg-accent-soft text-accent">
              <Icon path={iconPath.info} size={16} />
            </span>
            <span>
              Unde îl pui: <b className="text-ink">{fix.where_ro}</b>, apoi lipește textul și salvează.
            </span>
          </div>
        )}
      </PanelBody>
      <PanelFooter>
        <button
          type="button"
          onClick={handleCopyAndOpen}
          disabled={state.status !== "ready"}
          className={`${buttonVariant.primary} h-13 w-full text-base disabled:opacity-50`}
        >
          <Icon path={isCopied ? iconPath.check : screenIconPath.copy} size={18} strokeWidth={2.2} />
          {isCopied ? getCopiedLabel(fix.deep_link_label_ro) : (fix.deep_link_label_ro ?? "Copiază textul")}
        </button>
        <ResolveButton onResolve={onResolve} />
      </PanelFooter>
    </>
  );
}
