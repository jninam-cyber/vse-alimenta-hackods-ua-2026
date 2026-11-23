"""Emparejamiento explicable basado en reglas (no es un modelo de IA)."""
from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Any

from database import now_local


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _urgency_points(expiry_text: str) -> tuple[int, str]:
    try:
        hours = (datetime.fromisoformat(expiry_text) - now_local()).total_seconds() / 3600
    except (TypeError, ValueError):
        return 0, "No se pudo evaluar el plazo"
    if hours <= 6:
        return 20, "Plazo próximo: requiere coordinación prioritaria"
    if hours <= 24:
        return 12, "Disponible dentro de las próximas 24 horas"
    return 5, "Tiene un plazo de recojo más amplio"


def score_pair(donation: dict[str, Any], need: dict[str, Any]) -> dict[str, Any] | None:
    """Devuelve puntaje y explicación; descarta categorías incompatibles."""
    same_food = normalize(donation["food_name"]) == normalize(need["food_name"])
    same_category = normalize(donation["category"]) == normalize(need["category"])
    if not (same_food or same_category):
        return None

    score = 0
    reasons: list[str] = []
    if same_food:
        score += 50
        reasons.append("Coincide el alimento solicitado")
    else:
        score += 28
        reasons.append("Coincide el tipo de alimento")

    same_area = normalize(donation["area"]) == normalize(need["area"])
    if same_area:
        score += 20
        reasons.append("Se encuentran en la misma zona")
    else:
        score += 7
        reasons.append("Requiere coordinar el traslado entre zonas")

    urgency, urgency_reason = _urgency_points(donation["available_until"])
    score += urgency
    reasons.append(urgency_reason)

    donation_left = float(donation.get("remaining_kg", donation["quantity_kg"]))
    need_left = float(need.get("remaining_kg", need["quantity_kg"]))
    if donation_left >= need_left:
        score += 10
        reasons.append("La cantidad disponible cubre la necesidad pendiente")
    else:
        score += 6
        reasons.append("La donación cubre una parte de la necesidad")

    return {
        "score": min(score, 100),
        "reasons": reasons,
        "donation_remaining_kg": round(donation_left, 2),
        "need_remaining_kg": round(need_left, 2),
        "suggested_kg": round(min(donation_left, need_left), 2),
    }


def build_matches(donations: list[dict[str, Any]], needs: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    now = now_local()
    matches: list[dict[str, Any]] = []
    for donation in donations:
        if donation["status"] != "Disponible" or donation["remaining_kg"] <= 0:
            continue
        try:
            if datetime.fromisoformat(donation["available_until"]) < now:
                continue
        except ValueError:
            continue
        for need in needs:
            if need["status"] != "Activa" or need["remaining_kg"] <= 0:
                continue
            try:
                if datetime.fromisoformat(need["needed_until"]) < now:
                    continue
            except ValueError:
                continue
            pair = score_pair(donation, need)
            if pair is None:
                continue
            matches.append({"donation": donation, "need": need, **pair})

    matches.sort(key=lambda item: (item["score"], item["suggested_kg"]), reverse=True)
    return matches[:limit]
