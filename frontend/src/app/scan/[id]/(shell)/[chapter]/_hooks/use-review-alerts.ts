import { useCallback, useState } from "react";
import useSWR from "swr";
import type { ToastContent } from "@/components/Toast";
import { disableReviewAlerts, enableReviewAlerts, getReviewAlerts, simulateReviewAlert } from "@/lib/api";
import type { ReviewAlerts } from "@/lib/types";

/** An action on the review alerts that can be running. */
export type ReviewAlertAction = "enable" | "disable" | "simulate";

/** Loads the scan's WhatsApp review alerts and turns them on or off, or sends a simulated alert, with the action's state. */
export function useReviewAlerts(scanId: string) {
  const { data, error, isLoading, mutate } = useSWR<ReviewAlerts>(`review-alerts:${scanId}`, () => getReviewAlerts(scanId));
  const [pendingAction, setPendingAction] = useState<ReviewAlertAction | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [toast, setToast] = useState<ToastContent | null>(null);
  const dismissToast = useCallback(() => setToast(null), []);

  /** Turns the alerts on for a phone number. */
  async function enable(phone: string) {
    setPendingAction("enable");
    setActionError(null);
    try {
      await mutate(await enableReviewAlerts(scanId, phone), { revalidate: false });
    } catch (caught) {
      setActionError(caught);
    } finally {
      setPendingAction(null);
    }
  }

  /** Turns the alerts off. */
  async function disable() {
    setPendingAction("disable");
    setActionError(null);
    try {
      await mutate(await disableReviewAlerts(scanId), { revalidate: false });
    } catch (caught) {
      setActionError(caught);
    } finally {
      setPendingAction(null);
    }
  }

  /** Sends the alert for the newest review now; the delivery state is reloaded either way. */
  async function simulate() {
    setPendingAction("simulate");
    setActionError(null);
    try {
      const sent = await simulateReviewAlert(scanId);
      setToast({ title: "Trimis pe WhatsApp", detail: `Răspuns la recenzia de la ${sent.author}` });
    } catch (caught) {
      setActionError(caught);
    } finally {
      setPendingAction(null);
      void mutate();
    }
  }

  return {
    alerts: data,
    error,
    isLoading,
    retry: () => mutate(),
    pendingAction,
    actionError,
    enable,
    disable,
    simulate,
    toast,
    dismissToast,
  };
}
