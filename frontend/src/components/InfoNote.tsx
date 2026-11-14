import type { ReactNode } from "react";
import { Icon, iconPath } from "@/components/Icon";

/** A component that shows a soft blue note card with the info icon and the given text. */
export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-3xl bg-accent-soft px-5.5 py-5">
      <Icon path={iconPath.info} size={20} className="mt-px flex-none text-accent-strong" />
      <span className="text-sm leading-[1.55] text-accent-deep">{children}</span>
    </div>
  );
}
