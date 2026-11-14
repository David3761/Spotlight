import { APP_NAME } from "@/config";
import { iconPath } from "@/components/Icon";

/** A component that shows the product logo: the blue sparkle square and the product name. */
export function AppLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex size-9 items-center justify-center rounded-[11px] bg-accent">
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
          <path d={iconPath.sparkle} className="fill-white" />
        </svg>
      </div>
      <span className="text-[17px] font-extrabold tracking-[-0.01em]">{APP_NAME}</span>
    </div>
  );
}
