import { useEffect, useState } from "react";
import { generateFixText } from "@/lib/api";
import type { GeneratedText, Tone } from "@/lib/types";

/** What the text request is doing. */
type GeneratedTextState =
  | { status: "loading" }
  | { status: "error"; error: unknown }
  | { status: "ready"; result: GeneratedText };

/** The tone, variant and retry count that identify one request for a text. */
interface TextRequest {
  /** The tone the text is written in. */
  tone: Tone;
  /** The wording variant, starting at 0. */
  variant: number;
  /** How many times the owner retried after a failure. */
  attempt: number;
}

/** Writes a fix text for a problem, again whenever the tone or variant changes, and holds the owner's edits. */
export function useGeneratedText(scanId: string, checkId: string) {
  const [request, setRequest] = useState<TextRequest>({ tone: "prietenos", variant: 0, attempt: 0 });
  const [state, setState] = useState<GeneratedTextState>({ status: "loading" });
  const [text, setText] = useState("");

  useEffect(() => {
    let isCancelled = false;
    generateFixText(scanId, checkId, request.tone, request.variant).then(
      (result) => {
        if (isCancelled) {
          return;
        }
        setText(result.text);
        setState({ status: "ready", result });
      },
      (error: unknown) => {
        if (!isCancelled) {
          setState({ status: "error", error });
        }
      },
    );
    return () => {
      isCancelled = true;
    };
  }, [scanId, checkId, request]);

  /** Writes a new text in another tone, starting from its first variant. */
  const pickTone = (tone: Tone) => {
    if (tone === request.tone) {
      return;
    }
    setState({ status: "loading" });
    setRequest({ tone, variant: 0, attempt: 0 });
  };

  /** Writes another wording in the same tone. */
  const regenerate = () => {
    setState({ status: "loading" });
    setRequest({ ...request, variant: request.variant + 1 });
  };

  /** Repeats the failed request. */
  const retry = () => {
    setState({ status: "loading" });
    setRequest({ ...request, attempt: request.attempt + 1 });
  };

  return { tone: request.tone, state, text, setText, pickTone, regenerate, retry };
}
