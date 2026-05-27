"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  pending?: boolean;
  error?: boolean;
};

type ChatResponse = {
  reply: string;
};

const welcomeMessage: ChatMessage = {
  id: "assistant-welcome",
  role: "assistant",
  content: "Je suis l'assistante Sophie. Comment puis-je vous aider ?",
};

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function ClinicMark() {
  return (
    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-clinic to-accent text-white shadow-lg shadow-sky-900/20">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 640 640"
        className="h-7 w-7"
        aria-hidden="true"
      >
        <path
          d="M160 128C160 92.7 188.7 64 224 64L416 64C451.3 64 480 92.7 480 128L480 192L544 192C579.3 192 608 220.7 608 256L608 512C608 547.3 579.3 576 544 576L96 576C60.7 576 32 547.3 32 512L32 256C32 220.7 60.7 192 96 192L160 192L160 128zM304 416C286.3 416 272 430.3 272 448L272 528L368 528L368 448C368 430.3 353.7 416 336 416L304 416zM160 432L160 400C160 391.2 152.8 384 144 384L112 384C103.2 384 96 391.2 96 400L96 432C96 440.8 103.2 448 112 448L144 448C152.8 448 160 440.8 160 432zM144 320C152.8 320 160 312.8 160 304L160 272C160 263.2 152.8 256 144 256L112 256C103.2 256 96 263.2 96 272L96 304C96 312.8 103.2 320 112 320L144 320zM544 432L544 400C544 391.2 536.8 384 528 384L496 384C487.2 384 480 391.2 480 400L480 432C480 440.8 487.2 448 496 448L528 448C536.8 448 544 440.8 544 432zM528 320C536.8 320 544 312.8 544 304L544 272C544 263.2 536.8 256 528 256L496 256C487.2 256 480 263.2 480 272L480 304C480 312.8 487.2 320 496 320L528 320zM296 168L296 200L264 200C255.2 200 248 207.2 248 216L248 232C248 240.8 255.2 248 264 248L296 248L296 280C296 288.8 303.2 296 312 296L328 296C336.8 296 344 288.8 344 280L344 248L376 248C384.8 248 392 240.8 392 232L392 216C392 207.2 384.8 200 376 200L344 200L344 168C344 159.2 336.8 152 328 152L312 152C303.2 152 296 159.2 296 168z"
          fill="currentColor"
        />
      </svg>
    </div>
  );
}

export default function Home() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "";
  const [threadId, setThreadId] = useState("session-pending");
  const historyEndRef = useRef<HTMLDivElement | null>(null);
  const sendingRef = useRef(false);
  const [messages, setMessages] = useState<ChatMessage[]>([welcomeMessage]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rating, setRating] = useState(0);

  const canSubmit =
    input.trim().length > 0 && !loading && apiBaseUrl.length > 0;

  useEffect(() => {
    setThreadId(createId());
  }, []);

  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  function resetConversation() {
    if (loading || sendingRef.current) {
      return;
    }

    setMessages([welcomeMessage]);
    setInput("");
    setError("");
    setLoading(false);
    setRating(0);
    sendingRef.current = false;
    setThreadId(createId());
  }

  async function sendMessage(trimmedInput: string) {
    if (sendingRef.current) {
      return;
    }

    if (!apiBaseUrl) {
      setError("La variable NEXT_PUBLIC_API_BASE_URL n'est pas configuree.");
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmedInput,
    };
    const assistantMessageId = createId();

    setMessages((current) => [
      ...current,
      userMessage,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "L'assistant traite votre demande...",
        pending: true,
      },
    ]);
    setInput("");
    setLoading(true);
    setError("");
    sendingRef.current = true;

    try {
      const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmedInput,
          thread_id: threadId,
        }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as {
          detail?: string;
        } | null;
        throw new Error(payload?.detail ?? `Erreur API (${response.status})`);
      }

      const data = (await response.json()) as ChatResponse;
      const reply =
        data.reply?.trim() || "Le modele n'a renvoye aucune reponse.";

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: reply,
                pending: false,
                error: false,
              }
            : message,
        ),
      );
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Une erreur inattendue est survenue.";
      setError(message);
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantMessageId
            ? {
                ...item,
                content: `Erreur: ${message}`,
                pending: false,
                error: true,
              }
            : item,
        ),
      );
    } finally {
      setLoading(false);
      sendingRef.current = false;
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedInput = input.trim();
    if (!trimmedInput || loading) {
      return;
    }

    await sendMessage(trimmedInput);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) {
        void sendMessage(input.trim());
      }
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 text-ink sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-5xl items-center">
        <div className="w-full rounded-[2rem] border border-white/80 bg-white/75 p-4 shadow-glow backdrop-blur md:p-6">
          <div className="flex min-h-[76vh] flex-col overflow-hidden rounded-[1.75rem] border border-sky-100 bg-gradient-to-b from-white to-sky-50 p-5">
            <header className="flex items-start justify-between gap-4 border-b border-sky-100 pb-4">
              <div className="flex items-center gap-4">
                <ClinicMark />
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.26em] text-clinic">
                    Clinique Demo
                  </p>
                  <h1 className="text-3xl font-semibold tracking-tight text-clinicDark sm:text-4xl">
                    Assistant de clinique
                  </h1>
                </div>
              </div>

              <button
                type="button"
                onClick={resetConversation}
                disabled={loading}
                className="inline-flex items-center rounded-full border border-sky-200 bg-white px-4 py-2 text-sm font-medium text-clinic transition hover:border-sky-300 hover:bg-sky-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Nouvelle conversation
              </button>
            </header>

            <div className="mt-4 flex-1 overflow-hidden rounded-[1.5rem] border border-sky-100 bg-white">
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-sky-100 px-4 py-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">
                      Historique patient
                    </p>
                    <p className="text-xs text-slate-500">
                      Thread {threadId.slice(0, 8)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {loading ? (
                      <span className="rounded-full bg-clinicMint px-3 py-1 text-xs font-medium text-clinic">
                        Reponse en cours
                      </span>
                    ) : null}
                    <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
                      Support medical
                    </span>
                  </div>
                </div>

                <div className="flex-1 space-y-4 overflow-y-auto bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(244,249,253,0.96))] px-4 py-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[88%] rounded-3xl px-4 py-3 text-sm leading-6 shadow-sm sm:max-w-[76%] ${
                          message.role === "user"
                            ? "bg-gradient-to-br from-clinic to-accent text-white"
                            : message.error
                              ? "border border-rose-200 bg-rose-50 text-rose-800"
                              : "border border-sky-100 bg-white text-slate-800"
                        }`}
                      >
                        <div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] opacity-70">
                          <span>
                            {message.role === "user" ? "Vous" : "Clinique"}
                          </span>
                          {message.pending ? <span>- en cours</span> : null}
                        </div>
                        <div className="whitespace-pre-wrap">
                          {message.content}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={historyEndRef} />
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-3">
              <label
                htmlFor="message"
                className="block text-sm font-medium text-clinicDark"
              >
                Nouveau message
              </label>
              <textarea
                id="message"
                name="message"
                rows={4}
                value={input}
                onChange={(event) => {
                  setInput(event.target.value);
                  if (error) {
                    setError("");
                  }
                }}
                onKeyDown={handleComposerKeyDown}
                placeholder="Discutez avec l'assistant, par exemple : prise de rendez-vous, information patient, suivi..."
                className="w-full rounded-3xl border border-sky-200 bg-white px-4 py-3 text-base text-ink shadow-sm outline-none transition placeholder:text-slate-400 focus:border-clinic focus:ring-4 focus:ring-sky-100"
              />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="inline-flex items-center justify-center rounded-full bg-clinic px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-[#155e75] disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {loading ? "Envoi en cours..." : "Envoyer"}
                </button>
                <p className="text-sm text-muted">
                  {apiBaseUrl
                    ? `API: ${apiBaseUrl}`
                    : "Definis NEXT_PUBLIC_API_BASE_URL pour activer l'envoi."}
                </p>
              </div>
            </form>

            <section className="mt-4 rounded-2xl border border-sky-100 bg-white/90 px-4 py-4 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-clinicDark">
                    Évaluer l'échange
                  </p>
                  <p className="text-sm text-muted">
                    Donnez une note à la fin de la discussion.
                  </p>
                </div>
                <p className="text-xs text-slate-500">
                  {rating > 0 ? `Note donnée: ${rating}/5` : "Aucune note pour le moment"}
                </p>
              </div>

              <div className="mt-3 flex items-center gap-2">
                {Array.from({ length: 5 }, (_, index) => {
                  const value = index + 1;
                  const active = value <= rating;
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setRating(value)}
                      className={`inline-flex h-11 w-11 items-center justify-center rounded-full border text-xl transition ${
                        active
                          ? "border-amber-300 bg-amber-50 text-amber-500"
                          : "border-sky-100 bg-white text-slate-300 hover:border-sky-200 hover:text-amber-300"
                      }`}
                      aria-label={`Noter l'échange ${value} sur 5`}
                    >
                      ★
                    </button>
                  );
                })}
                {rating > 0 ? (
                  <button
                    type="button"
                    onClick={() => setRating(0)}
                    className="ml-2 text-sm font-medium text-slate-500 underline-offset-4 hover:underline"
                  >
                    Réinitialiser
                  </button>
                ) : null}
              </div>
            </section>

            {error ? (
              <div
                role="alert"
                className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
              >
                {error}
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
