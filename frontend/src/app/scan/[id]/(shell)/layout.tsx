import { Suspense } from "react";
import { ScanShell } from "@/components/ScanShell";

/** The layout of every scan page except the loading screen: loads the scan and adds the navigation. */
export default function ScanShellLayout({ children }: LayoutProps<"/scan/[id]">) {
  return (
    <Suspense fallback={<div aria-busy="true" className="min-h-screen bg-page" />}>
      <ScanShell>{children}</ScanShell>
    </Suspense>
  );
}
