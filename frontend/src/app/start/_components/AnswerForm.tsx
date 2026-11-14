"use client";

import { useState, type FormEvent } from "react";
import { Icon, iconPath } from "@/components/Icon";

/** One text input of an answer form. */
export interface AnswerField {
  /** The input's accessible label. */
  label: string;
  /** The hint shown while the input is empty. */
  placeholder: string;
  /** The keyboard the input opens on mobile. */
  inputMode: "text" | "url";
  /** Whether the form can be sent with this input empty. */
  isOptional?: boolean;
  /** The icon shown inside the input. */
  icon?: string;
}

/** A component that shows the owner's text answer bar: one or more inputs and a send button. */
export function AnswerForm({
  fields,
  isDisabled,
  onSubmit,
}: {
  fields: AnswerField[];
  isDisabled: boolean;
  onSubmit: (values: string[]) => void;
}) {
  const [values, setValues] = useState(() => fields.map(() => ""));
  const canSend = fields.every((field, index) => field.isOptional || values[index].trim() !== "");

  /** Sends the trimmed values when every required input is filled. */
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend || isDisabled) {
      return;
    }
    onSubmit(values.map((value) => value.trim()));
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3 border-t border-divider px-4 py-4 lg:px-6">
      <div className="flex min-w-0 flex-1 flex-col gap-2 lg:flex-row">
        {fields.map((field, index) => (
          <label
            key={field.label}
            className="flex min-h-13 min-w-0 flex-1 items-center gap-2.5 rounded-[26px] bg-fill px-4.5 text-muted focus-within:outline-2 focus-within:outline-accent"
          >
            <span className="sr-only">{field.label}</span>
            {field.icon ? <Icon path={field.icon} size={18} className="shrink-0" /> : null}
            <input
              type="text"
              inputMode={field.inputMode}
              value={values[index]}
              placeholder={field.placeholder}
              disabled={isDisabled}
              autoFocus={index === 0}
              onChange={(event) => setValues(values.map((value, at) => (at === index ? event.target.value : value)))}
              className="min-w-0 flex-1 bg-transparent py-3 text-[15px] text-ink outline-none placeholder:text-muted"
            />
          </label>
        ))}
      </div>
      <button
        type="submit"
        aria-label="Trimite"
        disabled={!canSend || isDisabled}
        className="flex size-13 shrink-0 cursor-pointer items-center justify-center rounded-full bg-accent text-white hover:bg-accent-hover disabled:cursor-default disabled:opacity-50"
      >
        <Icon path={iconPath.arrowUp} size={20} strokeWidth={2.2} />
      </button>
    </form>
  );
}
