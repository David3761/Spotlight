import { replyIndent } from "@/app/start/_components/QuickReplies";
import { getCandidateMeta } from "@/app/start/_hooks/onboarding-model";
import { buttonVariant } from "@/components/button-styles";
import { chapterIconPath, Icon } from "@/components/Icon";
import type { PlaceCandidate } from "@/lib/types";

/** A component that shows the Google places found for the business, to pick one. */
export function PlaceCandidates({
  candidates,
  isDisabled,
  onPick,
}: {
  candidates: PlaceCandidate[];
  isDisabled: boolean;
  onPick: (candidate: PlaceCandidate) => void;
}) {
  return (
    <div className={replyIndent}>
      <ul className="m-0 grid list-none grid-cols-[repeat(auto-fill,minmax(11rem,1fr))] gap-3 p-0">
        {candidates.map((candidate) => (
          <li
            key={candidate.place_id}
            className={`flex flex-col gap-3 rounded-[20px] bg-surface p-4 ${candidate.best ? "border-2 border-accent" : "border border-border"}`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="flex size-11 items-center justify-center rounded-[14px] bg-accent-soft text-accent">
                <Icon path={chapterIconPath.profil} size={22} />
              </span>
              {candidate.best ? (
                <span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-bold text-accent-strong">
                  Cel mai probabil
                </span>
              ) : null}
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[15px] font-bold">{candidate.name}</span>
              <span className="text-[13px] text-muted">{candidate.address}</span>
              <span className="text-[13px] font-semibold text-subtle">{getCandidateMeta(candidate)}</span>
            </div>
            <button
              type="button"
              disabled={isDisabled}
              onClick={() => onPick(candidate)}
              className={`${candidate.best ? buttonVariant.primary : buttonVariant.outline} mt-auto h-11 cursor-pointer text-sm disabled:cursor-default disabled:opacity-60`}
            >
              Asta sunt eu
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
