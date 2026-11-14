import { usePathname, useRouter, useSearchParams } from "next/navigation";

/** Reads and changes which fix panel is open through the `?fix=` search param. */
export function useFixPanel() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  /** Opens the panel of a problem as a new history entry. */
  const open = (checkId: string) => {
    router.push(`${pathname}?fix=${encodeURIComponent(checkId)}`, { scroll: false });
  };

  /** Closes the open panel by removing the param. */
  const close = () => {
    router.replace(pathname, { scroll: false });
  };

  return { checkId: searchParams.get("fix"), open, close };
}
