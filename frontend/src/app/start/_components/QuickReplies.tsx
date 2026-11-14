import { chipVariant } from "@/components/button-styles";
import { Icon, iconPath } from "@/components/Icon";

/** The look of every quick-reply chip, besides its pressed or idle colours. */
const chipSize = "inline-flex h-11 cursor-pointer items-center gap-1.5 px-3.5 text-sm disabled:cursor-default disabled:opacity-60";

/** The indent that lines chips up under the assistant's bubbles. */
export const replyIndent = "ps-9 lg:ps-11";

/** A component that shows a row of single-choice chips; choosing one answers the question. */
export function QuickReplies<Option extends { label: string }>({
  groupLabel,
  options,
  isDisabled,
  onSelect,
}: {
  groupLabel: string;
  options: readonly Option[];
  isDisabled: boolean;
  onSelect: (option: Option) => void;
}) {
  return (
    <div role="group" aria-label={groupLabel} className={`flex flex-wrap gap-2 ${replyIndent}`}>
      {options.map((option) => (
        <button
          key={option.label}
          type="button"
          disabled={isDisabled}
          onClick={() => onSelect(option)}
          className={`${chipVariant.idle} ${chipSize}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** A component that shows a row of multi-choice chips with a check on the chosen ones. */
export function ToggleReplies<Value extends string>({
  groupLabel,
  options,
  chosen,
  isDisabled,
  onToggle,
}: {
  groupLabel: string;
  options: readonly { label: string; value: Value }[];
  chosen: readonly Value[];
  isDisabled: boolean;
  onToggle: (value: Value) => void;
}) {
  return (
    <div role="group" aria-label={groupLabel} className={`flex flex-wrap gap-2 ${replyIndent}`}>
      {options.map((option) => {
        const isChosen = chosen.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isChosen}
            disabled={isDisabled}
            onClick={() => onToggle(option.value)}
            className={`${isChosen ? chipVariant.pressed : chipVariant.idle} ${chipSize}`}
          >
            {isChosen ? <Icon path={iconPath.check} size={14} strokeWidth={3} /> : null}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
