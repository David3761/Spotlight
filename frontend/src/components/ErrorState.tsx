import { ApiError } from "@/lib/api";
import { buttonVariant } from "@/components/button-styles";

/** Returns the message to show the owner for a failed request. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.messageRo) {
      return error.messageRo;
    }
    if (error.code === "network") {
      return "Nu am putut contacta serverul.";
    }
  }
  return "Ceva nu a mers. Încearcă din nou.";
}

/** A component that shows why a load failed, with a retry button. */
export function ErrorState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-4 rounded-[28px] border border-border bg-surface p-6">
      <p className="text-[15px] font-medium text-body">{getErrorMessage(error)}</p>
      <button type="button" onClick={onRetry} className={`${buttonVariant.primary} h-12 px-6 text-[15px]`}>
        Încearcă din nou
      </button>
    </div>
  );
}
