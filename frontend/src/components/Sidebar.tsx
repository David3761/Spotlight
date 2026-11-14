import Link from "next/link";
import { AppLogo } from "@/components/AppLogo";
import { chapterIconPath, Icon, iconPath } from "@/components/Icon";
import type { Chapter, Report } from "@/lib/types";

/** The sidebar entry that matches the current route. */
export type SidebarSection = "panou" | "gemini" | "conversatii" | Chapter["id"] | null;

/** Returns the screen-reader label of a chapter's open-problem badge. */
function getCountLabel(count: number): string {
  return count === 1 ? "1 problemă nerezolvată" : `${count} probleme nerezolvate`;
}

/** A component that shows the desktop navigation: business, main pages, conversations and the 8 chapters. */
export function Sidebar({ report, active }: { report: Report; active: SidebarSection }) {
  const base = `/scan/${report.scan_id}`;
  const { business, gemini } = report;
  const mainItems = [
    { key: "panou", name: "Panou principal", href: base, icon: iconPath.home, meta: null },
    {
      key: "gemini",
      name: "Vizibilitate în Gemini",
      href: `${base}/gemini`,
      icon: iconPath.target,
      meta: `${gemini.mentioned}/${gemini.total}`,
    },
  ];

  return (
    <nav aria-label="Meniu principal" className="flex min-h-screen w-full flex-col gap-5 bg-surface px-4.5 py-6 text-ink">
      <div className="px-1.5">
        <AppLogo />
      </div>

      <div className="flex w-full items-center gap-3 rounded-[18px] border border-border bg-page p-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-[13px] bg-accent-soft text-[15px] font-extrabold text-accent-strong">
          {business.initials}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="text-sm font-bold">{business.name}</span>
          <span className="text-xs text-muted">
            {business.type_label_ro} · {business.neighborhood}
          </span>
        </span>
        <Icon path={iconPath.chevronDown} size={18} className="text-muted" />
      </div>

      <div className="flex flex-col gap-1">
        {mainItems.map((item) => {
          const isActive = item.key === active;
          return (
            <Link
              key={item.key}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={`flex min-h-11.5 items-center gap-3 rounded-[14px] px-3 text-sm ${
                isActive ? "bg-accent-soft font-bold text-accent-strong" : "font-semibold text-body"
              }`}
            >
              <Icon path={item.icon} size={20} />
              <span className="flex-1">{item.name}</span>
              {item.meta && <span className="text-xs font-bold text-muted">{item.meta}</span>}
            </Link>
          );
        })}
        <Link
          href={`${base}/conversatii`}
          aria-current={active === "conversatii" ? "page" : undefined}
          className={`mt-1.5 flex min-h-14 items-center gap-3 rounded-2xl border-2 bg-accent-soft px-3 py-2 text-accent-deep ${
            active === "conversatii" ? "border-accent" : "border-transparent"
          }`}
        >
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface text-accent">
            <Icon path={iconPath.chat} size={18} />
          </span>
          <span className="flex flex-1 flex-col gap-px">
            <span className="text-sm font-extrabold">Conversații</span>
            <span className="text-xs font-semibold text-accent-muted">Vorbește cu asistentul</span>
          </span>
          <Icon path={iconPath.chevronRight} size={16} strokeWidth={2.4} className="text-accent" />
        </Link>
      </div>

      <div className="flex flex-col gap-0.5">
        <div className="flex items-baseline justify-between px-3 pb-1.5">
          <span className="text-xs font-bold tracking-[0.08em] text-muted uppercase">Capitole</span>
          <span className="text-[11px] font-semibold text-muted">de rezolvat</span>
        </div>
        {report.chapters.map((chapter) => (
          <SidebarChapter key={chapter.id} chapter={chapter} href={`${base}/${chapter.id}`} isActive={chapter.id === active} />
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-1 border-t border-divider pt-3">
        <div className="flex min-h-11 items-center gap-3 rounded-[14px] px-3 text-sm font-semibold text-body">
          <Icon path={iconPath.store} size={20} />
          Datele afacerii
        </div>
        <div className="flex min-h-11 items-center gap-3 rounded-[14px] px-3 text-sm font-semibold text-body">
          <Icon path={iconPath.help} size={20} />
          Ajutor
        </div>
      </div>
    </nav>
  );
}

/** A component that shows one chapter link with its open-problem count or an all-solved check. */
function SidebarChapter({ chapter, href, isActive }: { chapter: Chapter; href: string; isActive: boolean }) {
  const count = chapter.problems.length;
  return (
    <Link
      href={href}
      aria-current={isActive ? "page" : undefined}
      className={`flex min-h-11 items-center gap-3 rounded-[14px] px-3 py-1.5 text-sm leading-[1.3] ${
        isActive ? "bg-accent-soft font-bold text-accent-strong" : "font-semibold text-body"
      }`}
    >
      <Icon path={chapterIconPath[chapter.id]} size={20} className={`shrink-0 ${isActive ? "text-accent" : "text-muted"}`} />
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span>{chapter.name_ro}</span>
        {chapter.start_here && (
          <span className="flex items-center gap-1 text-[11px] font-bold text-accent-hover">
            <svg width="11" height="11" viewBox="0 0 24 24" aria-hidden="true">
              <path d={iconPath.sparkle} className="fill-accent" />
            </svg>
            Începe de aici
          </span>
        )}
      </span>
      {chapter.has_fixes && count > 0 && (
        <span
          aria-label={getCountLabel(count)}
          className={`flex h-6 min-w-6.5 items-center justify-center rounded-full px-2 text-[13px] font-extrabold ${
            isActive ? "bg-accent text-white" : "bg-fill text-body"
          }`}
        >
          {count}
        </span>
      )}
      {chapter.has_fixes && count === 0 && (
        <span aria-label="Totul rezolvat" className="flex size-6 items-center justify-center rounded-full bg-high text-white">
          <Icon path={iconPath.check} size={13} strokeWidth={3.2} />
        </span>
      )}
    </Link>
  );
}
