import { iconPath } from "@/components/Icon";

/** A component that shows the assistant's round sparkle badge; the class sets its size. */
export function AssistantAvatar({ className = "size-7 lg:size-8" }: { className?: string }) {
  return (
    <div className={`flex shrink-0 items-center justify-center rounded-full bg-accent-soft ${className}`}>
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-1/2">
        <path d={iconPath.sparkle} className="fill-accent" />
      </svg>
    </div>
  );
}
