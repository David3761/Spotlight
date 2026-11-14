import { linkOffIcon } from "@/app/start/_hooks/onboarding-model";
import { buttonVariant } from "@/components/button-styles";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { Icon, iconPath } from "@/components/Icon";

/** The look of the three recovery buttons' shared size. */
const actionSize = "h-11 cursor-pointer text-sm disabled:cursor-default disabled:opacity-60";

/** A component that explains a Google Maps link couldn't be read and offers the ways forward. */
export function LinkError({
  isDisabled,
  onSearch,
  onPasteLink,
  onSkip,
}: {
  isDisabled: boolean;
  onSearch: () => void;
  onPasteLink: () => void;
  onSkip: () => void;
}) {
  return (
    <div className="flex items-start gap-2 lg:gap-3">
      <AssistantAvatar />
      <div
        role="alert"
        className="flex min-w-0 flex-col gap-3.5 rounded-[22px] rounded-es-[6px] border border-low-line bg-surface p-4 lg:max-w-150 lg:p-5"
      >
        <div className="flex items-start gap-3.5">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-[14px] bg-low-tint text-low-text">
            <Icon path={linkOffIcon} size={22} />
          </span>
          <div className="flex min-w-0 flex-col gap-1.5">
            <span className="text-[17px] font-extrabold">Nu am putut deschide acest link</span>
            <span className="text-[15px] leading-[1.55] text-body">
              Nicio grijă, se întâmplă des. Pare că linkul s-a tăiat la copiere. În Google Maps, deschide cafeneaua,
              apasă <b>Distribuie</b> și copiază linkul de acolo.
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2.5 lg:ps-13.5">
          <button
            type="button"
            disabled={isDisabled}
            onClick={onSearch}
            className={`${buttonVariant.primary} ${actionSize} px-5`}
          >
            <Icon path={iconPath.search} size={16} strokeWidth={2.2} />
            Caută-mă pe Google
          </button>
          <button
            type="button"
            disabled={isDisabled}
            onClick={onPasteLink}
            className={`${buttonVariant.outline} ${actionSize} px-5`}
          >
            Lipesc alt link
          </button>
          <button
            type="button"
            disabled={isDisabled}
            onClick={onSkip}
            className={`${actionSize} px-2 font-semibold text-subtle`}
          >
            Sar peste, îl adaug mai târziu
          </button>
        </div>
      </div>
    </div>
  );
}
