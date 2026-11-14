/** The looks of each {@link PointsBadge} size: a fixed one, and one that grows on desktop. */
const sizeClass = {
  fixed: "size-13 rounded-2xl text-[17px]",
  responsive: "size-12 rounded-[15px] text-base lg:size-15 lg:rounded-[18px] lg:text-[19px] lg:tracking-[-0.02em]",
};

/** The props of {@link PointsBadge}. */
interface PointsBadgeProps {
  /** The points a problem is worth. */
  points: number;
  /** The tile's size: the same at every width, or growing on desktop. */
  size: keyof typeof sizeClass;
}

/** A component that shows the "+N" green tile with the points a problem is worth. */
export function PointsBadge({ points, size }: PointsBadgeProps) {
  return (
    <span className={`flex shrink-0 items-center justify-center bg-high-tint font-extrabold text-high-text ${sizeClass[size]}`}>
      <span aria-hidden="true">+{points}</span>
      <span className="sr-only">{points} puncte</span>
    </span>
  );
}
