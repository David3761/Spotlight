import { ErrorState } from "@/components/ErrorState";
import { useDevExport } from "../_hooks/use-dev-export";
import { downloadFile } from "./download-file";
import { HandoffFooter } from "./HandoffFooter";
import { LoadingBlock } from "./LoadingBlock";
import { PanelBody, PanelFooter, ResolveButton } from "./PanelParts";

/** A component that shows the Markdown instructions for the web developer, with download and message. */
export function DevExportPanel({ scanId, onResolve }: { scanId: string; onResolve: () => void }) {
  const { devExport, error, retry } = useDevExport(scanId);

  /** Downloads the instructions as a Markdown file. */
  const handleDownload = () => {
    if (devExport) {
      downloadFile("instructiuni-site.md", devExport.markdown, "text/markdown");
    }
  };

  return (
    <>
      <PanelBody className="bg-fill">
        {error && <ErrorState error={error} onRetry={retry} />}
        {!error && !devExport && <LoadingBlock label="Pregătim instrucțiunile…" />}
        {devExport && (
          <>
            <pre
              aria-label="Previzualizare instrucțiuni"
              className="rounded-2xl bg-surface p-5 font-mono text-[13px] leading-[1.6] break-words whitespace-pre-wrap text-body shadow-[0_1px_2px_rgba(15,23,42,0.06),0_8px_24px_rgba(15,23,42,0.08)]"
            >
              {devExport.markdown}
            </pre>
            <span className="px-1 text-[13px] text-subtle">
              Instrucțiunile sunt pentru persoana care îți face site-ul. Trimite-i-le și bifează „Am rezolvat” după ce le aplică.
            </span>
          </>
        )}
      </PanelBody>
      {devExport ? (
        <HandoffFooter message={devExport.message_ro} onDownload={handleDownload} onResolve={onResolve} />
      ) : (
        <PanelFooter>
          <ResolveButton onResolve={onResolve} />
        </PanelFooter>
      )}
    </>
  );
}
