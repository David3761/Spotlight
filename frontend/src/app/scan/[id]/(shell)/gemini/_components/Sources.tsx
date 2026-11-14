import type { Source } from "@/lib/types";

/** A component that lists the sources Gemini used for an answer, attributing Maps sources to Google Maps. */
export function Sources({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return null;
  }
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted">
      <span className="font-semibold">Surse:</span>
      <ul className="flex flex-wrap gap-x-3 gap-y-1">
        {sources.map((source, index) => (
          <li key={`${source.uri}-${index}`}>
            <a
              href={source.uri}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted underline hover:text-accent-hover"
            >
              {source.title}
            </a>
            {source.kind === "maps" && (
              <>
                {" · "}
                <span translate="no">Google Maps</span>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
