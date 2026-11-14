import { Suspense } from "react";
import { Loading } from "./_components/Loading";

/** The analysis loading route; the client part reads the scan ID, so it sits inside a Suspense boundary. */
export default function LoadingPage() {
  return (
    <Suspense fallback={<div aria-busy="true" className="min-h-screen bg-page" />}>
      <Loading />
    </Suspense>
  );
}
