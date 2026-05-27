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
  content: "Bonjour. Je suis l'assistant de la clinique. Ecris un message pour commencer.",
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
      <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" aria-hidden="true">
        <path
          d="M12 5v14M5 12h14"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
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

  const canSubmit = input.trim().length > 0 && !loading && apiBaseUrl.length > 0;

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
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(payload?.detail ?? `Erreur API (${response.status})`);
      }

      const data = (await response.json()) as ChatResponse;
      const reply = data.reply?.trim() || "Le modele n'a renvoye aucune reponse.";

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
      const message = err instanceof Error ? err.message : "Une erreur inattendue est survenue.";
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
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-muted sm:text-base">
                    Interface de chat rassurante, inspiree des codes visuels medicals, avec
                    historique, reponses du modele et nouvelle conversation en un clic.
                  </p>
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
                    <p className="text-xs text-slate-500">Thread {threadId.slice(0, 8)}</p>
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
                          <span>{message.role === "user" ? "Vous" : "Clinique"}</span>
                          {message.pending ? <span>- en cours</span> : null}
                        </div>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      </div>
                    </div>
                  ))}
                  <div ref={historyEndRef} />
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-3">
              <label htmlFor="message" className="block text-sm font-medium text-clinicDark">
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
                placeholder="Pose ta demande, par exemple : prise de rendez-vous, information patient, suivi..."
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
