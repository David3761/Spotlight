import Link from "next/link";
import { Icon, iconPath } from "@/components/Icon";

/** A component that links back to the dashboard: a bar with a back button on mobile, a text link on desktop. */
export function BackLink({ scanId }: { scanId: string }) {
  return (
    <>
      <header className="flex items-center gap-1 px-3 py-2.5 lg:hidden">
        <Link
          href={`/scan/${scanId}`}
          aria-label="Înapoi la panou"
          className="flex size-11 items-center justify-center rounded-full text-body"
        >
          <Icon path={iconPath.back} size={22} strokeWidth={2.2} />
        </Link>
        <span className="text-[15px] font-bold text-subtle">Panou</span>
      </header>
      <Link
        href={`/scan/${scanId}`}
        className="hidden min-h-11 items-center gap-1.5 self-start text-sm font-bold text-subtle lg:flex"
      >
        <Icon path={iconPath.back} size={18} strokeWidth={2.2} />
        Panou principal
      </Link>
    </>
  );
}
