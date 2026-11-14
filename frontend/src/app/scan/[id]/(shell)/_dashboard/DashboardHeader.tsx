import { Icon, iconPath } from "@/components/Icon";
import { getDayLabel } from "@/lib/format";
import type { Business } from "@/lib/types";

/** The look shared by the desktop and mobile rescan buttons. */
const rescanButtonClass =
  "flex items-center justify-center rounded-full border border-border bg-surface text-body disabled:opacity-60";

/** The props of {@link DashboardHeader}. */
interface DashboardHeaderProps {
  /** The analysed business. */
  business: Business;
  /** When the analysis ran. */
  checkedAt: string;
  /** When `true`, a rescan request is in flight and the button is disabled. */
  isRescanning: boolean;
  /** Called when the owner asks for a new analysis. */
  onRescan: () => void;
}

/** A component that shows the greeting and the rescan button: a heading on desktop, a compact bar on mobile. */
export function DashboardHeader({ business, checkedAt, isRescanning, onRescan }: DashboardHeaderProps) {
  const checkedDay = getDayLabel(checkedAt);
  const lastChecked = checkedDay ? `Ultima analiză: ${checkedDay}` : null;

  return (
    <>
      <div className="hidden flex-wrap items-end justify-between gap-4 lg:flex">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[32px] font-extrabold tracking-[-0.02em]">Bună, {business.name}</h1>
          {lastChecked && <span className="text-sm text-muted">{lastChecked}</span>}
        </div>
        <button
          type="button"
          onClick={onRescan}
          disabled={isRescanning}
          className={`${rescanButtonClass} h-11 gap-2 px-4.5 text-sm font-bold`}
        >
          <Icon path={iconPath.refresh} size={18} />
          Analizează din nou
        </button>
      </div>
      <header className="flex items-center gap-3 pt-4 pe-4 ps-5 pb-2 lg:hidden">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-[13px] bg-accent-soft text-sm font-extrabold text-accent-strong">
          {business.initials}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="text-base font-extrabold">{business.name}</span>
          {lastChecked && <span className="text-xs text-muted">{lastChecked}</span>}
        </span>
        <button
          type="button"
          aria-label="Analizează din nou"
          onClick={onRescan}
          disabled={isRescanning}
          className={`${rescanButtonClass} size-11`}
        >
          <Icon path={iconPath.refresh} size={20} />
        </button>
      </header>
    </>
  );
}
