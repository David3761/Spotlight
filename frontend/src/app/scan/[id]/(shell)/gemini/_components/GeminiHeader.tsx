import { BackLink } from "@/components/BackLink";
import { ScoreRing } from "@/components/ScoreRing";
import { Icon, iconPath } from "@/components/Icon";
import { getErrorMessage } from "@/components/ErrorState";
import { buttonVariant } from "@/components/button-styles";
import { getDayLabel } from "@/lib/format";
import type { GeminiBlock } from "@/lib/types";

/** The path of the back icon. */

/** The path of the retry icon. */

/** The props of {@link GeminiHeader}. */
interface GeminiHeaderProps {
  /** The scan's ID. */
  scanId: string;
  /** The live Gemini test. */
  gemini: GeminiBlock;
  /** When `true`, the test is running. */
  isTesting: boolean;
  /** When `true`, the test just finished in this session. */
  hasRetested: boolean;
  /** The error of the last failed run; `null` when there is none. */
  error: unknown;
  /** Starts the test again. */
  onRetest: () => void;
}

/** Returns the "last checked" line, or `null` when the date can't be read. */
function getLastCheckedText(lastChecked: string, isTesting: boolean, hasRetested: boolean): string | null {
  if (isTesting) {
    return "Îi punem din nou cele 12 întrebări…";
  }
  if (hasRetested) {
    return "Ultima verificare: acum câteva secunde";
  }
  const date = new Date(lastChecked);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return `Ultima verificare: ${getDayLabel(date)}`;
}

/** A component that shows the back link, the Gemini score, the intro and the retest button. */
export function GeminiHeader({ scanId, gemini, isTesting, hasRetested, error, onRetest }: GeminiHeaderProps) {
  const lastCheckedText = getLastCheckedText(gemini.last_checked, isTesting, hasRetested);

  return (
    <>
      <BackLink scanId={scanId} />

      <section className="flex flex-col items-center gap-2.5 px-5 pb-5 text-center lg:flex-row lg:flex-wrap lg:gap-7 lg:rounded-[28px] lg:border lg:border-border lg:bg-surface lg:px-8 lg:py-7 lg:text-start">
        <div className="lg:hidden">
          <ScoreRing score={gemini.score} size={120} thick={14} />
        </div>
        <div className="hidden lg:block">
          <ScoreRing score={gemini.score} size={128} thick={14} />
        </div>
        <div className="contents lg:flex lg:flex-1 lg:basis-90 lg:flex-col lg:gap-2">
          <h1 className="mt-1 text-2xl font-extrabold tracking-[-0.02em] lg:m-0 lg:text-[30px]">Vizibilitate în Gemini</h1>
          {gemini.status === "complete" ? (
            <span className="text-base font-bold text-accent-deep lg:text-lg">
              Apari în {gemini.mentioned} din {gemini.total} răspunsuri
            </span>
          ) : (
            <span className="text-base font-bold text-accent-deep lg:text-lg">Testul nu a putut rula.</span>
          )}
          <p className="max-w-155 text-sm leading-normal text-subtle lg:hidden">
            I-am pus lui Gemini 12 întrebări, cum le-ar pune clienții tăi.
          </p>
          <p className="hidden max-w-155 text-[15px] leading-[1.55] text-subtle lg:block">
            I-am pus lui Gemini 12 întrebări, exact cum le-ar pune clienții tăi. Mai jos vezi ce a răspuns și pe cine a
            recomandat.
          </p>
        </div>
        <div className="contents lg:flex lg:flex-col lg:items-end lg:gap-2">
          <button
            type="button"
            onClick={onRetest}
            aria-busy={isTesting}
            className={`${buttonVariant.primary} mt-1.5 h-12.5 w-full gap-2.5 text-[15px] lg:mt-0 lg:h-12 lg:w-auto lg:px-5.5`}
          >
            {isTesting ? (
              <span
                aria-hidden="true"
                className="size-4.5 animate-[spin_0.8s_linear_infinite] rounded-full border-[2.5px] border-white/35 border-t-white"
              />
            ) : (
              <Icon path={iconPath.refresh} size={18} strokeWidth={2.2} />
            )}
            {isTesting ? "Testăm…" : "Testează din nou"}
          </button>
          {lastCheckedText && (
            <span role="status" className="text-[13px] font-semibold text-muted">
              {lastCheckedText}
            </span>
          )}
          {error !== null && (
            <span role="alert" className="max-w-80 text-[13px] font-semibold text-low-text lg:text-end">
              {getErrorMessage(error)}
            </span>
          )}
        </div>
      </section>
    </>
  );
}
