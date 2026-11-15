"use client";

import { type FormEvent, useState } from "react";
import { ErrorState, getErrorMessage } from "@/components/ErrorState";
import { Toast } from "@/components/Toast";
import { buttonVariant } from "@/components/button-styles";
import type { ReviewAlerts } from "@/lib/types";
import { type ReviewAlertAction, useReviewAlerts } from "../_hooks/use-review-alerts";

/** A component that lets the owner get a suggested reply on WhatsApp for every new Google review. */
export function ReviewAlertsCard({ scanId }: { scanId: string }) {
  const { alerts, error, isLoading, retry, pendingAction, actionError, enable, disable, simulate, toast, dismissToast } =
    useReviewAlerts(scanId);

  return (
    <section aria-labelledby="review-alerts-title" className="flex flex-col gap-3 rounded-3xl border border-border bg-surface p-6">
      <h2 id="review-alerts-title" className="text-base font-extrabold">
        Răspunsuri sugerate pe WhatsApp
      </h2>
      {isLoading && <div aria-busy="true" className="h-24 animate-pulse rounded-2xl bg-fill" />}
      {!isLoading && error && <ErrorState error={error} onRetry={retry} />}
      {alerts && !alerts.enabled && <ReviewAlertsOff pendingAction={pendingAction} onEnable={enable} />}
      {alerts?.enabled && (
        <ReviewAlertsOn
          alerts={alerts}
          pendingAction={pendingAction}
          deliveryProblem={actionError === null ? alerts.delivery_problem_ro : null}
          onDisable={disable}
          onSimulate={simulate}
        />
      )}
      {actionError !== null && (
        <p role="alert" className="text-[13px] leading-normal font-semibold text-low-text">
          {getErrorMessage(actionError)}
        </p>
      )}
      <Toast toast={toast} onDismiss={dismissToast} />
    </section>
  );
}

/** A component that explains the alerts and asks for the owner's WhatsApp number. */
function ReviewAlertsOff({
  pendingAction,
  onEnable,
}: {
  pendingAction: ReviewAlertAction | null;
  onEnable: (phone: string) => void;
}) {
  const [phone, setPhone] = useState("");

  /** Turns the alerts on for the typed number. */
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onEnable(phone.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <p className="text-sm leading-[1.55] text-subtle">
        Când primești o recenzie nouă pe Google, îți trimitem pe WhatsApp un răspuns pe care îl poți copia.
      </p>
      <label className="flex flex-col gap-1.5 text-[13px] font-bold text-body">
        Numărul tău de WhatsApp
        <input
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="0722 123 456"
          className="min-h-12 rounded-2xl border border-border bg-surface px-4 py-2.5 text-[15px] font-medium text-ink outline-none focus-visible:border-accent"
        />
      </label>
      <button
        type="submit"
        disabled={phone.trim() === "" || pendingAction !== null}
        aria-busy={pendingAction === "enable"}
        className={`${buttonVariant.primary} min-h-12 px-5 text-[15px] disabled:opacity-60`}
      >
        {pendingAction === "enable" ? "Pornim…" : "Pornește"}
      </button>
    </form>
  );
}

/** A component that shows the alerts are on, the „Start” step, a failed delivery and the demo and stop buttons. */
function ReviewAlertsOn({
  alerts,
  pendingAction,
  deliveryProblem,
  onDisable,
  onSimulate,
}: {
  alerts: ReviewAlerts;
  pendingAction: ReviewAlertAction | null;
  deliveryProblem: string | null;
  onDisable: () => void;
  onSimulate: () => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm leading-[1.55] text-subtle">
        Pornit pentru <b className="text-ink">{alerts.phone}</b>. Verificăm recenziile noi de două ori pe zi.
      </p>
      {deliveryProblem && (
        <p role="alert" className="text-[13px] leading-normal font-semibold text-low-text">
          {deliveryProblem}
        </p>
      )}
      {alerts.whatsapp_link && (
        <>
          <p className="text-[13px] leading-normal text-subtle">
            Ca să-ți putem scrie, trimite-ne o dată «Start» pe WhatsApp. Mesajele ajung timp de 24 de ore după ultimul tău
            mesaj către noi.
          </p>
          <a
            href={alerts.whatsapp_link}
            target="_blank"
            rel="noreferrer"
            className={`${buttonVariant.outline} min-h-12 px-5 py-2.5 text-center text-[15px]`}
          >
            Trimite «Start» pe WhatsApp
          </a>
        </>
      )}
      {alerts.can_simulate && (
        <button
          type="button"
          onClick={onSimulate}
          disabled={pendingAction !== null}
          aria-busy={pendingAction === "simulate"}
          className={`${buttonVariant.soft} min-h-12 px-5 text-[15px] disabled:opacity-60`}
        >
          {pendingAction === "simulate" ? "Trimitem…" : "Simulează o recenzie nouă"}
        </button>
      )}
      <button
        type="button"
        onClick={onDisable}
        disabled={pendingAction !== null}
        className="self-start text-sm font-bold text-accent-strong underline-offset-2 hover:underline disabled:opacity-60"
      >
        Oprește mesajele
      </button>
    </div>
  );
}
