import { Icon, iconPath } from "@/components/Icon";
import { InfoNote } from "@/components/InfoNote";

/** What the owner can ask the assistant, each one starting a conversation. */
const ideas = [
  "Am adăugat programul de sărbători, marchează-l ca rezolvat",
  "Scrie-mi o postare pentru Profilul Google",
  "De ce nu apar la „cafenea unde pot lucra cu laptopul”?",
  "Ce fac prima dată azi?",
];

/** A component that shows the ideas to ask the assistant and the note about marking problems as fixed. */
export function AssistantIdeas({ isDisabled, onPick }: { isDisabled: boolean; onPick: (text: string) => void }) {
  return (
    <aside className="hidden max-w-95 flex-[1_1_300px] flex-col gap-4 lg:flex">
      <div className="flex flex-col gap-3.5 rounded-3xl border border-border bg-surface p-6">
        <span className="text-base font-extrabold">Ce poți să-i ceri</span>
        {ideas.map((idea) => (
          <button
            key={idea}
            type="button"
            disabled={isDisabled}
            onClick={() => onPick(idea)}
            className="flex min-h-12 items-center gap-2.5 rounded-2xl bg-page px-3.5 py-3 text-start text-sm leading-[1.4] font-semibold text-ink disabled:opacity-60"
          >
            <Icon path={iconPath.sparkle} size={16} strokeWidth={0} className="flex-none fill-accent" />
            {idea}
          </button>
        ))}
      </div>
      <InfoNote>
        Asistentul marchează o problemă ca rezolvată doar când îi spui tu. Verificăm din nou pe Google la următoarea analiză.
      </InfoNote>
    </aside>
  );
}
