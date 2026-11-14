"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useSWRConfig } from "swr";
import { buttonVariant } from "@/components/button-styles";
import { ErrorCard, ErrorState } from "@/components/ErrorState";
import { ApiError } from "@/lib/api";
import { useIsDesktop } from "@/hooks/use-is-desktop";
import { getScanKey, useScan } from "@/hooks/use-scan";
import { useScanProgress } from "../_hooks/use-scan-progress";
import { AnalysisSpinner } from "./AnalysisSpinner";
import { LoadingFrame } from "./LoadingFrame";
import { StepList } from "./StepList";
import { getProgressPercent, steps } from "./steps";

/** A component that shows the analysis progress and sends the owner to the results when it completes. */
export function Loading() {
  const { id: scanId } = useParams<{ id: string }>();
  const router = useRouter();
  const isDesktop = useIsDesktop();
  const isDesktopRef = useRef(isDesktop);
  const { mutate } = useSWRConfig();
  const { report } = useScan(scanId);
  const { doneDetails, outcome, failureMessage, retry } = useScanProgress(scanId);

  useEffect(() => {
    isDesktopRef.current = isDesktop;
  }, [isDesktop]);

  useEffect(() => {
    if (outcome !== "complete") {
      return;
    }
    // The cached envelope still says "running", which would send the shell back here, so drop it.
    void mutate(getScanKey(scanId), undefined, { revalidate: false });
    if (isDesktopRef.current) {
      router.replace(`/scan/${scanId}`);
    }
  }, [outcome, scanId, mutate, router]);

  const doneCount = Object.keys(doneDetails).length;
  const business = report?.business;
  const businessLine = business ? `${business.name} · ${business.neighborhood}` : null;

  if (outcome === "failed") {
    return (
      <LoadingFrame businessLine={businessLine}>
        <div className="mx-auto w-full max-w-xl">
          <ErrorCard message={failureMessage}>
            <Link href="/start" className={`${buttonVariant.primary} h-12 px-6 text-[15px]`}>
              Încearcă din nou
            </Link>
          </ErrorCard>
        </div>
      </LoadingFrame>
    );
  }
  if (outcome === "disconnected") {
    return (
      <LoadingFrame businessLine={businessLine}>
        <div className="mx-auto w-full max-w-xl">
          <ErrorState error={new ApiError("network", null, null)} onRetry={retry} />
        </div>
      </LoadingFrame>
    );
  }

  return (
    <LoadingFrame businessLine={businessLine}>
      <section
        aria-live="polite"
        className="flex flex-col items-center gap-7 lg:flex-[0_1_600px] lg:gap-6 lg:rounded-4xl lg:border lg:border-border lg:bg-surface lg:p-10 lg:shadow-[0_1px_2px_rgba(15,23,42,0.04),0_16px_40px_rgba(15,23,42,0.06)]"
      >
        <div className="flex flex-col items-center gap-5 text-center lg:gap-6">
          <span className="lg:hidden">
            <AnalysisSpinner size={112} radius={48} starSize={34} />
          </span>
          <span className="hidden lg:block">
            <AnalysisSpinner size={128} radius={56} starSize={40} />
          </span>
          <div className="flex flex-col items-center gap-1.5 lg:gap-2">
            <h1 className="text-[26px] font-extrabold tracking-[-0.02em] lg:text-[32px]">Analizăm afacerea ta…</h1>
            <p className="max-w-110 text-sm leading-normal text-subtle lg:text-[15px] lg:leading-normal">
              Durează cam un minut.
              <span className="hidden lg:inline">
                {" "}
                Ne uităm unde apare {business?.name ?? "afacerea ta"} și ce află Gemini despre ea.
              </span>
            </p>
          </div>
        </div>
        <StepList doneDetails={doneDetails} />
        <div className="flex w-full flex-col gap-2">
          <div className="h-2.5 overflow-hidden rounded-[5px] bg-border lg:bg-divider">
            <div
              className="h-2.5 rounded-[5px] bg-accent transition-[width] duration-600 ease-in-out"
              style={{ width: `${getProgressPercent(doneCount)}%` }}
            />
          </div>
          <span className="text-center text-[13px] font-semibold text-subtle">
            {doneCount >= steps.length ? (
              <>
                <span className="hidden lg:inline">Gata! Pregătim rezultatele…</span>
                <span className="lg:hidden">Gata!</span>
              </>
            ) : (
              `${doneCount} din ${steps.length} pași gata`
            )}
          </span>
        </div>
      </section>

      <aside className="hidden flex-[0_1_320px] flex-col gap-4 lg:flex">
        <div className="flex flex-col gap-2.5 rounded-3xl bg-accent-soft p-6">
          <span className="text-xs font-bold tracking-[0.08em] text-accent-strong uppercase">Știai că?</span>
          <p className="text-[15px] leading-[1.55] text-accent-deep">
            Gemini citește și ce scriu clienții în recenzii, de exemplu „cafea bună” sau „loc liniștit pentru laptop”, ca să
            știe pe cine să recomande.
          </p>
        </div>
        <div className="flex flex-col gap-2.5 rounded-3xl border border-border bg-surface p-6">
          <span className="text-[15px] font-bold">Ce urmează</span>
          <p className="text-sm leading-[1.55] text-subtle">
            Primești un scor general și o listă scurtă de lucruri de rezolvat, în ordinea în care contează cel mai mult.
          </p>
        </div>
      </aside>

      <div className="mt-auto flex flex-col gap-2 rounded-[20px] bg-accent-soft px-4.5 py-4 lg:hidden">
        <span className="text-xs font-bold tracking-[0.08em] text-accent-strong uppercase">Știai că?</span>
        <p className="text-sm leading-normal text-accent-deep">
          Gemini citește și ce scriu clienții în recenzii, ca să știe pe cine să recomande.
        </p>
      </div>
      {outcome === "complete" && (
        <Link href={`/scan/${scanId}`} className={`${buttonVariant.primary} h-13 text-[15px] lg:hidden`}>
          Vezi rezultatele
        </Link>
      )}
    </LoadingFrame>
  );
}
