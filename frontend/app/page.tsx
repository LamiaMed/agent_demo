"use client";

import { FormEvent, useState } from "react";

type ChatResponse = {
  reply: string;
};

export default function Home() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "";
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = question.trim().length > 0 && !loading && apiBaseUrl.length > 0;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) {
      return;
    }

    if (!apiBaseUrl) {
      setError("La variable NEXT_PUBLIC_API_BASE_URL n’est pas configurée.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmedQuestion }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(payload?.detail ?? `Erreur API (${response.status})`);
      }

      const data = (await response.json()) as ChatResponse;
      setAnswer(data.reply ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur inattendue est survenue.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-10 text-ink sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-4xl items-center">
        <div className="w-full rounded-[2rem] border border-white/70 bg-panel/90 p-6 shadow-glow backdrop-blur sm:p-8">
          <div className="mb-8 space-y-3">
            <p className="text-sm font-medium uppercase tracking-[0.24em] text-accent">
              Agent IA
            </p>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Pose une question à l’agent
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted sm:text-base">
              Cette interface appelle l’API FastAPI via <code className="font-mono">NEXT_PUBLIC_API_BASE_URL</code>.
              La clé OpenAI reste côté backend.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <label htmlFor="question" className="block text-sm font-medium text-ink">
              Ta question
            </label>
            <textarea
              id="question"
              name="question"
              rows={5}
              value={question}
              onChange={(event) => {
                setQuestion(event.target.value);
                if (error) {
                  setError("");
                }
              }}
              placeholder="Exemple : donne-moi un rendez-vous pour vendredi prochain à 11h."
              className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-base text-ink shadow-sm outline-none transition placeholder:text-stone-400 focus:border-accent focus:ring-4 focus:ring-accentSoft"
            />

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                type="submit"
                disabled={!canSubmit}
                className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-stone-300"
              >
                {loading ? "Envoi en cours..." : "Envoyer"}
              </button>
              <p className="text-sm text-muted">
                {apiBaseUrl ? `API: ${apiBaseUrl}` : "Définis NEXT_PUBLIC_API_BASE_URL pour activer l’envoi."}
              </p>
            </div>
          </form>

          <section className="mt-8 grid gap-4">
            <div className="rounded-2xl border border-stone-200 bg-white p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted">
                  Réponse
                </h2>
                {loading ? (
                  <span className="rounded-full bg-accentSoft px-3 py-1 text-xs font-medium text-accent">
                    Chargement...
                  </span>
                ) : null}
              </div>
              <div className="min-h-32 whitespace-pre-wrap rounded-xl bg-stone-50 p-4 font-mono text-sm leading-6 text-stone-700">
                {answer || "La réponse de l’agent apparaîtra ici."}
              </div>
            </div>

            {error ? (
              <div
                role="alert"
                className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
              >
                {error}
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}
