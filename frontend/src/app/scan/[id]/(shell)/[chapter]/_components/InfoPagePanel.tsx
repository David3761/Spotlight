import type { ReactNode } from "react";
import { ErrorState } from "@/components/ErrorState";
import type { InfoPage } from "@/lib/types";
import { useInfoPage } from "../_hooks/use-info-page";
import { downloadFile } from "./download-file";
import { HandoffFooter } from "./HandoffFooter";
import { LoadingBlock } from "./LoadingBlock";
import { PanelBody, PanelFooter, ResolveButton } from "./PanelParts";

/** The look of a field the owner still has to fill in. */
const fillMark = "rounded-md bg-mid-tint px-1.5 py-px font-bold text-mid-text";

/** The look of the small uppercase label above each block of the preview. */
const blockLabel = "text-xs font-bold tracking-[0.06em] text-muted uppercase";

/** A component that shows a block of the preview under its label. */
function PreviewBlock({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className={blockLabel}>{label}</span>
      {children}
    </div>
  );
}

/** A component that draws the info page the way a visitor sees it, with the fields to fill in marked. */
function InfoPagePreview({ infoPage }: { infoPage: InfoPage }) {
  return (
    <article
      aria-label="Previzualizare pagină de informații"
      className="flex flex-col gap-4.5 rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(15,23,42,0.06),0_8px_24px_rgba(15,23,42,0.08)] lg:rounded-[18px] lg:px-7.5 lg:py-7"
    >
      {infoPage.suggested_url && (
        <span className="self-start rounded-full bg-page px-2.5 py-1 text-xs font-semibold text-muted">
          {infoPage.suggested_url}
        </span>
      )}
      <div className="flex flex-col gap-1">
        <h3 className="text-xl font-extrabold tracking-[-0.01em] lg:text-2xl">{infoPage.title}</h3>
        <span className="text-[13px] font-semibold text-subtle lg:text-sm">{infoPage.subtitle}</span>
      </div>
      <p className="text-[13px] leading-[1.6] text-body lg:text-sm">{infoPage.description}</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {(infoPage.address || infoPage.area_note) && (
          <PreviewBlock label="Adresă și zonă">
            {infoPage.address && <span className="text-sm leading-normal">{infoPage.address}</span>}
            {infoPage.area_note && <span className="text-[13px] text-subtle">{infoPage.area_note}</span>}
          </PreviewBlock>
        )}
        <PreviewBlock label="Program">
          {infoPage.hours.map((line) => (
            <span key={line} className="text-sm leading-normal">
              {line}
            </span>
          ))}
          <span className="text-sm leading-normal">
            Sărbători: {infoPage.holiday_hours ?? <mark className={fillMark}>de completat</mark>}
          </span>
        </PreviewBlock>
        <PreviewBlock label="Contact">
          <span className="text-sm leading-normal">
            Telefon: {infoPage.phone ?? <mark className={fillMark}>numărul tău</mark>}
          </span>
          {infoPage.instagram && <span className="text-sm leading-normal">Instagram: {infoPage.instagram}</span>}
        </PreviewBlock>
        {infoPage.also_on.length > 0 && (
          <PreviewBlock label="Ne găsești și pe">
            <span className="text-sm leading-normal">{infoPage.also_on.join(", ")}</span>
          </PreviewBlock>
        )}
      </div>
      {infoPage.menu.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className={blockLabel}>Ce servim</span>
          <ul className="flex flex-wrap gap-1.5">
            {infoPage.menu.map((item) => (
              <li key={item} className="rounded-full border border-border bg-page px-3 py-1.25 text-[13px] font-semibold">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
      {infoPage.faq.length > 0 && (
        <div className="flex flex-col gap-2.5">
          <span className={blockLabel}>Întrebări frecvente</span>
          {infoPage.faq.map((entry) => (
            <div key={entry.q} className="flex flex-col gap-0.5">
              <span className="text-sm font-bold">{entry.q}</span>
              <span className="text-sm text-subtle">{entry.a}</span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

/** A component that previews the generated info page, downloads it and helps send it to the web developer. */
export function InfoPagePanel({ scanId, onResolve }: { scanId: string; onResolve: () => void }) {
  const { infoPage, error, retry } = useInfoPage(scanId);

  /** Downloads the page as an HTML file. */
  const handleDownload = () => {
    if (infoPage) {
      downloadFile("pagina-informatii.html", infoPage.html, "text/html");
    }
  };

  return (
    <>
      <PanelBody className="bg-fill">
        {error && <ErrorState error={error} onRetry={retry} />}
        {!error && !infoPage && <LoadingBlock label="Pregătim pagina…" />}
        {infoPage && (
          <>
            <InfoPagePreview infoPage={infoPage} />
            {infoPage.to_fill.length > 0 && (
              <span className="px-1 text-[13px] text-subtle">Ce e marcat cu galben completezi tu înainte s-o trimiți.</span>
            )}
          </>
        )}
      </PanelBody>
      {infoPage ? (
        <HandoffFooter message={infoPage.message_ro} onDownload={handleDownload} onResolve={onResolve} />
      ) : (
        <PanelFooter>
          <ResolveButton onResolve={onResolve} />
        </PanelFooter>
      )}
    </>
  );
}
