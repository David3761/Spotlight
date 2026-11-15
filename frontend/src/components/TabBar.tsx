import Link from "next/link";
import { Icon, iconPath } from "@/components/Icon";

/** The tab that matches the current route. */
export type Tab = "acasa" | "gemini" | "capitole" | "asistent" | null;

/** A component that shows the mobile bottom navigation; „Capitole” opens the first chapter. */
export function TabBar({ scanId, active }: { scanId: string; active: Tab }) {
  const base = `/scan/${scanId}`;
  const tabs = [
    { key: "acasa", name: "Acasă", href: base, icon: iconPath.home },
    { key: "gemini", name: "LLM", href: `${base}/gemini`, icon: iconPath.geminiBubble },
    { key: "capitole", name: "Capitole", href: `${base}/profil`, icon: iconPath.grid },
    { key: "asistent", name: "Asistent", href: `${base}/conversatii`, icon: iconPath.chat },
  ];

  return (
    <nav
      aria-label="Navigare"
      className="grid h-22 w-full grid-cols-4 gap-1 border-t border-border bg-surface px-3 pt-2 pb-5.5"
    >
      {tabs.map((tab) => {
        const isActive = tab.key === active;
        return (
          <Link
            key={tab.key}
            href={tab.href}
            aria-current={isActive ? "page" : undefined}
            className={`flex min-h-13 flex-col items-center justify-center gap-1 rounded-[14px] text-[11px] font-bold ${
              isActive ? "text-accent-strong" : "text-muted"
            }`}
          >
            <span className={`flex h-7.5 w-14 items-center justify-center rounded-full ${isActive ? "bg-accent-soft" : ""}`}>
              <Icon path={tab.icon} size={22} />
            </span>
            {tab.name}
          </Link>
        );
      })}
    </nav>
  );
}
