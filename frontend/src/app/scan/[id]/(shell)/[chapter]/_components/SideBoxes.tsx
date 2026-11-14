import { Icon } from "@/components/Icon";
import { ScoreRing } from "@/components/ScoreRing";
import { screenIconPath } from "./icons";

/** A component that shows what the chapter and overall scores would be once every open problem is fixed. */
export function AllFixedBox({
  chapterScore,
  chapterScoreIfFixed,
  overall,
  overallGain,
}: {
  chapterScore: number | null;
  chapterScoreIfFixed: number;
  overall: number;
  overallGain: number;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-border bg-surface p-6">
      <span className="text-base font-extrabold">Dacă rezolvi tot</span>
      <div className="flex items-center justify-center gap-4">
        <ScoreRing score={chapterScore} size={76} />
        <Icon path={screenIconPath.arrowRight} size={28} strokeWidth={2.2} className="text-faint" />
        <ScoreRing score={chapterScoreIfFixed} size={76} />
      </div>
      <p className="text-sm leading-[1.55] text-subtle">
        Scorul general ar crește cu aproximativ <b className="text-ink">{overallGain} puncte</b>, de la {overall} la{" "}
        {overall + overallGain}.
      </p>
    </div>
  );
}

/** A component that tells the owner where this chapter's problems get fixed. */
export function WhereToFixBox({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-2.5 rounded-3xl bg-accent-soft p-6">
      <span className="text-base font-extrabold text-accent-deep">Unde se rezolvă</span>
      <p className="text-sm leading-[1.55] text-accent-deep">{text}</p>
    </div>
  );
}
