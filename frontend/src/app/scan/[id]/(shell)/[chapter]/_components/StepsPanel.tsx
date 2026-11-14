import { buttonVariant } from "@/components/button-styles";
import { Icon } from "@/components/Icon";
import type { Problem } from "@/lib/types";
import { screenIconPath } from "./icons";
import { PanelBody, PanelFooter, ResolveButton } from "./PanelParts";

/** A component that shows why a problem matters, what was found and the numbered steps to fix it. */
export function StepsPanel({ problem, onResolve }: { problem: Problem; onResolve: () => void }) {
  const { fix } = problem;
  return (
    <>
      <PanelBody>
        <p className="rounded-2xl bg-page px-4 py-3.5 text-sm leading-[1.55] text-subtle">{problem.why_ro}</p>
        {fix.evidence_ro && (
          <p className="rounded-2xl bg-accent-soft px-4 py-3.5 text-sm leading-[1.55] font-semibold text-accent-deep">
            {fix.evidence_ro}
          </p>
        )}
        <ol className="flex flex-col gap-3.5">
          {fix.steps_ro.map((step, index) => (
            <li key={step} className="flex items-start gap-3 text-[15px] leading-normal text-body">
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-sm font-extrabold text-accent-strong">
                {index + 1}
              </span>
              <span className="pt-0.5">{step}</span>
            </li>
          ))}
        </ol>
      </PanelBody>
      <PanelFooter>
        {fix.deep_link && (
          <a
            href={fix.deep_link}
            target="_blank"
            rel="noopener noreferrer"
            className={`${buttonVariant.primary} h-13 w-full text-base`}
          >
            {fix.deep_link_label_ro ?? "Deschide"}
            <Icon path={screenIconPath.external} size={17} />
          </a>
        )}
        <ResolveButton onResolve={onResolve} />
      </PanelFooter>
    </>
  );
}
