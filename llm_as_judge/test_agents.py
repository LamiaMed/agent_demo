from __future__ import annotations

import csv
import json
import os
import argparse
from pathlib import Path
from statistics import mean
from typing import Any

import pytest
import requests
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_CSV = PROJECT_ROOT / "references" / "questions_generated.csv"
DEFAULT_RESULTS_CSV = PROJECT_ROOT / "llm_as_judge" / "results_agents.csv"
AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8000")
CHAT_ENDPOINT = f"{AGENT_URL.rstrip('/')}/chat"
HEALTH_ENDPOINT = f"{AGENT_URL.rstrip('/')}/health"
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
REQUEST_TIMEOUT = float(os.getenv("AGENT_TIMEOUT", "120"))
GLOBAL_THRESHOLD = float(os.getenv("LLM_JUDGE_THRESHOLD", "3.0"))
load_dotenv()

def load_questions(path: Path = QUESTIONS_CSV) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV introuvable: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        return list(reader)


def wait_for_agent_api() -> None:
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        response.raise_for_status()
    except Exception as error:
        pytest.fail(
            "L'API FastAPI n'est pas accessible. Lance d'abord `uvicorn app:app --reload`.\n"
            f"Détails: {error}"
        )


def ask_agent(question: str) -> str:
    payload = {"message": question}
    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    reply = data.get("reply", "")
    if not reply:
        raise AssertionError(f"Réponse vide retournée par l'agent pour: {question}")
    return str(reply)


def build_judge_llm() -> ChatOpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.fail(
            "OPENAI_API_KEY est manquant. Configure la clé avant de lancer le juge LLM."
        )
    return ChatOpenAI(model=JUDGE_MODEL, temperature=0)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Réponse JSON introuvable dans: {text}")

    return json.loads(cleaned[start : end + 1])


def judge_answer(
    question: str,
    expected_answer: str,
    agent_answer: str,
    question_type: str,
) -> dict[str, Any]:
    llm = build_judge_llm()
    prompt = f"""
Tu es un juge LLM chargé d'évaluer la réponse d'un agent conversationnel.

Contexte:
- Question: {question}
- Type de question: {question_type}
- Réponse attendue: {expected_answer}
- Réponse de l'agent: {agent_answer}

Règles d'évaluation:
- Note chaque critère de 1 à 5.
- relevance: pertinence par rapport à la question.
- faithfulness: fidélité aux documents / au besoin demandé.
- coherence: clarté, structure, absence de contradictions.
- overall: moyenne globale de l'évaluation.

Pour les questions:
- in_corpus / in_corpus_detailed / reformulation: la réponse doit être factuellement correcte et proche de la réponse attendue.
- out_of_corpus: la réponse doit dire que l'information n'est pas dans les documents ou refuser correctement.
- ambiguous / too_broad: la réponse doit demander une précision avant de répondre.

Retourne uniquement un JSON valide avec exactement ces clés:
{{
  "relevance": 1,
  "faithfulness": 1,
  "coherence": 1,
  "overall": 1,
  "rationale": "court commentaire"
}}
"""
    response = llm.invoke(prompt)
    raw_text = response.content if hasattr(response, "content") else str(response)
    return _extract_json(raw_text)


def evaluate_row(row: dict[str, str]) -> dict[str, Any]:
    question = row["question"]
    expected_answer = row["expected_answer"]
    question_type = row["type"]

    agent_answer = ask_agent(question)
    judgment = judge_answer(question, expected_answer, agent_answer, question_type)

    scores = [
        float(judgment["relevance"]),
        float(judgment["faithfulness"]),
        float(judgment["coherence"]),
    ]

    return {
        "id": row["id"],
        "question": question,
        "type": question_type,
        "expected_answer": expected_answer,
        "agent_answer": agent_answer,
        "judgment": judgment,
        "average_score": mean(scores),
    }


def write_results_csv(results: list[dict[str, Any]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "question",
        "type",
        "expected_answer",
        "agent_answer",
        "relevance",
        "faithfulness",
        "coherence",
        "overall",
        "average_score",
        "rationale",
    ]

    with output_csv.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for item in results:
            judgment = item["judgment"]
            writer.writerow(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "type": item["type"],
                    "expected_answer": item["expected_answer"],
                    "agent_answer": item["agent_answer"],
                    "relevance": judgment.get("relevance", ""),
                    "faithfulness": judgment.get("faithfulness", ""),
                    "coherence": judgment.get("coherence", ""),
                    "overall": judgment.get("overall", ""),
                    "average_score": f'{item["average_score"]:.2f}',
                    "rationale": judgment.get("rationale", ""),
                }
            )


def run_evaluation(
    questions_csv: Path = QUESTIONS_CSV,
    output_csv: Path = DEFAULT_RESULTS_CSV,
    threshold: float = GLOBAL_THRESHOLD,
) -> dict[str, Any]:
    wait_for_agent_api()
    rows = load_questions(questions_csv)

    results = [evaluate_row(row) for row in rows]
    global_average = mean(item["average_score"] for item in results)

    write_results_csv(results, output_csv)

    summary = {
        "questions_csv": str(questions_csv),
        "output_csv": str(output_csv),
        "count": len(results),
        "global_average": global_average,
        "threshold": threshold,
        "passed": global_average >= threshold,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def test_agent_with_llm_as_a_judge() -> None:
    summary = run_evaluation()
    assert summary["passed"] is True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Évalue l'agent FastAPI avec un LLM-as-a-judge et exporte les résultats."
    )
    parser.add_argument(
        "--questions-csv",
        type=Path,
        default=QUESTIONS_CSV,
        help="Chemin du CSV de questions.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DEFAULT_RESULTS_CSV,
        help="Chemin du CSV de sortie.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=GLOBAL_THRESHOLD,
        help="Seuil minimal de score global.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_evaluation(
        questions_csv=args.questions_csv,
        output_csv=args.output_csv,
        threshold=args.threshold,
    )
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
