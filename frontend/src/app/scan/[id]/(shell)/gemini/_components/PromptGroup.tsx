import { Icon, iconPath } from "@/components/Icon";
import { Sources } from "./Sources";
import type { GeminiGroup, GeminiPrompt } from "@/lib/types";

/** A component that shows one group of prompts with its score and every prompt's result. */
export function PromptGroup({ group }: { group: GeminiGroup }) {
  const hasMentions = group.mentioned > 0;

  return (
    <section className="flex min-w-0 flex-col rounded-[22px] border border-border bg-surface px-4 pt-4 pb-1.5 lg:basis-75 lg:flex-1 lg:gap-1.5 lg:rounded-3xl lg:p-5.5">
      <div className="flex items-center justify-between gap-2.5 pb-2 lg:items-start lg:gap-3 lg:pb-2.5">
        <div className="flex flex-col gap-0.5 lg:gap-0.75">
          <h2 className="text-[17px] font-extrabold lg:text-lg">{group.name_ro}</h2>
          <span className="text-xs text-muted lg:text-[13px]">{group.desc_ro}</span>
        </div>
        <span
          className={`flex h-7 items-center rounded-full px-2.5 text-xs font-extrabold whitespace-nowrap lg:h-7.5 lg:px-3 lg:text-[13px] ${
            hasMentions ? "bg-high-tint text-high-text" : "bg-low-tint text-low-text"
          }`}
        >
          <span className="hidden lg:inline">Apari în&nbsp;</span>
          {group.mentioned} din {group.total}
        </span>
      </div>
      {group.prompts.map((prompt) => (
        <PromptRow key={prompt.text} prompt={prompt} />
      ))}
    </section>
  );
}

/** A component that shows one prompt, whether the business appears, who else was recommended and the sources. */
function PromptRow({ prompt }: { prompt: GeminiPrompt }) {
  return (
    <div className="flex items-start gap-3 border-t border-fill py-3 lg:flex-col lg:gap-2 lg:py-3.5">
      {prompt.mentioned ? (
        <>
          <span
            role="img"
            aria-label="Apari"
            className="flex size-6.5 flex-none items-center justify-center rounded-full bg-high text-white lg:hidden"
          >
            <Icon path={iconPath.check} size={14} strokeWidth={3.2} />
          </span>
          <span className="hidden h-6.5 items-center gap-1.5 self-start rounded-full bg-high-tint ps-1 pe-2.5 text-xs font-bold text-high-text lg:flex">
            <span className="flex size-4.5 items-center justify-center rounded-full bg-high text-white">
              <Icon path={iconPath.check} size={11} strokeWidth={3.5} />
            </span>
            Apari
          </span>
        </>
      ) : (
        <>
          <span
            role="img"
            aria-label="Nu apari"
            className="flex size-6.5 flex-none items-center justify-center rounded-full bg-low-tint text-low-text lg:hidden"
          >
            <Icon path={iconPath.cross} size={13} strokeWidth={3.2} />
          </span>
          <span className="hidden h-6.5 items-center gap-1.5 self-start rounded-full bg-low-tint ps-1 pe-2.5 text-xs font-bold text-low-text lg:flex">
            <span className="flex size-4.5 items-center justify-center rounded-full bg-low text-white">
              <Icon path={iconPath.cross} size={11} strokeWidth={3.5} />
            </span>
            Nu apari
          </span>
        </>
      )}
      <div className="flex min-w-0 flex-1 flex-col gap-0.75 lg:flex-none lg:gap-2">
        <span className="text-sm leading-[1.4] font-bold lg:text-[15px]">„{prompt.text}”</span>
        {prompt.others.length > 0 && (
          <span className="text-xs leading-[1.4] text-subtle lg:text-[13px] lg:leading-[1.45]">
            {prompt.mentioned ? (
              <>
                <span className="lg:hidden">Alături de:</span>
                <span className="hidden lg:inline">Ai apărut alături de:</span>
              </>
            ) : (
              <>
                <span className="lg:hidden">Recomandate:</span>
                <span className="hidden lg:inline">LLM-ul a recomandat:</span>
              </>
            )}{" "}
            <b className="font-bold text-ink">{prompt.others.join(", ")}</b>
          </span>
        )}
        <Sources sources={prompt.sources} />
      </div>
    </div>
  );
}
