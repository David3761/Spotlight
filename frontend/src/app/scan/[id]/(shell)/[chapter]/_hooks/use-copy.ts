import { useConfirmation } from "./use-confirmation";

/** Copies text to the clipboard and tells whether it just worked. */
export function useCopy() {
  const { isConfirmed, confirm } = useConfirmation();

  /** Writes the text to the clipboard and confirms; a refused write confirms nothing. */
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      confirm();
    } catch {
      return;
    }
  };

  return { isCopied: isConfirmed, copy };
}
