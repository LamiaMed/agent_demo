import time, json, logging
from datetime import datetime

metrics = {
    "total": 0, "erreurs": 0,
    "latence_totale": 0, "cout_total": 0,
    "fallbacks": 0, 
    "nbr_rdv": 0
}

def log_request(question, latency_ms, tokens_in, tokens_out, error=None, fallback=False):
    # Estimer le coût (GPT-4o)
    cost = (tokens_in * 2.5 + tokens_out * 10) / 1_000_000
    metrics["total"] += 1
    metrics["latence_totale"] += latency_ms
    metrics["cout_total"] += cost
    if error: metrics["erreurs"] += 1
    if fallback: metrics["fallbacks"] += 1

def get_dashboard():
    n = metrics["total"] or 1
    return {
        "total_requetes": n,
        "latence_moy_ms": metrics["latence_totale"] // n,
        "taux_erreur": f"{metrics['erreurs']/n*100:.1f}%",
        "cout_total": f"{metrics['cout_total']:.2f} $",
        "nbr_rdv": metrics["nbr_rdv"],
    }