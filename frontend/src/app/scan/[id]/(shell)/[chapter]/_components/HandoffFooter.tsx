"use client";

import { useState } from "react";
import { buttonVariant } from "@/components/button-styles";
import { Icon, iconPath } from "@/components/Icon";
import { useConfirmation } from "../_hooks/use-confirmation";
import { useCopy } from "../_hooks/use-copy";
import { screenIconPath } from "./icons";
import { PanelFooter, ResolveButton } from "./PanelParts";

/** A component that offers the download, the message to the web developer and „Am rezolvat” under a document panel. */
export function HandoffFooter({
  message,
  onDownload,
  onResolve,
}: {
  message: string;
  onDownload: () => void;
  onResolve: () => void;
}) {
  const [isMessageOpen, setIsMessageOpen] = useState(false);
  const [text, setText] = useState(message);
  const { isConfirmed: isDownloaded, confirm: confirmDownload } = useConfirmation();
  const { isCopied, copy } = useCopy();

  /** Downloads the document and flips the label to „Descărcat”. */
  const handleDownload = () => {
    onDownload();
    confirmDownload();
  };

  return (
    <>
      {isMessageOpen && (
        <section
          aria-labelledby="handoff-title"
          className="flex flex-col gap-3 border-t border-border bg-surface px-5 pt-5 pb-5 shadow-[0_-12px_28px_rgba(15,23,42,0.08)] lg:px-7 lg:pb-6"
        >
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              aria-label="Înapoi la document"
              onClick={() => setIsMessageOpen(false)}
              className="flex size-10 items-center justify-center rounded-full bg-fill text-body"
            >
              <Icon path={iconPath.chevronDown} size={18} strokeWidth={2.2} />
            </button>
            <label id="handoff-title" htmlFor="handoff-text" className="text-base font-extrabold">
              Mesaj pregătit, îl poți schimba
            </label>
          </div>
          <textarea
            id="handoff-text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={5}
            className="w-full resize-y rounded-2xl border-2 border-accent-outline bg-surface px-4 py-3.5 text-[15px] leading-[1.55] text-ink outline-none focus:border-accent"
          />
          <div className="flex flex-wrap gap-2">
            <a
              href={`https://wa.me/?text=${encodeURIComponent(text)}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`${buttonVariant.primary} h-12 flex-[1_1_140px] text-[15px]`}
            >
              Trimite pe WhatsApp
            </a>
            <a
              href={`mailto:?body=${encodeURIComponent(text)}`}
              className={`${buttonVariant.outline} h-12 flex-[1_1_140px] text-[15px]`}
            >
              Trimite pe e-mail
            </a>
            <button
              type="button"
              onClick={() => copy(text)}
              className={`${buttonVariant.soft} h-12 flex-[1_1_120px] text-[15px]`}
            >
              {isCopied ? "Copiat" : "Copiază"}
            </button>
          </div>
        </section>
      )}
      <PanelFooter>
        {!isMessageOpen && (
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              onClick={handleDownload}
              className={`${buttonVariant.primary} h-13 flex-[1_1_180px] text-base`}
            >
              <Icon path={isDownloaded ? iconPath.check : screenIconPath.download} size={18} strokeWidth={2.2} />
              {isDownloaded ? "Descărcat" : "Descarcă"}
            </button>
            <button
              type="button"
              onClick={() => setIsMessageOpen(true)}
              className={`${buttonVariant.outline} h-13 flex-[2_1_280px] text-base`}
            >
              <Icon path={screenIconPath.send} size={18} strokeWidth={2.2} />
              Trimite persoanei care îți face site-ul
            </button>
          </div>
        )}
        <ResolveButton onResolve={onResolve} />
      </PanelFooter>
    </>
  );
}
