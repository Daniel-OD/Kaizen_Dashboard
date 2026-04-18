"""Core business calculations for Kaizen Dashboard.

Business rules:
  nr_echipe       = min(GIS, RASR)          — returns 0 when either is 0
  ore_an          = ore_sapt * sapt_an * (nr_echipe + FOL * pctFOL / 100)
  rata_medie      = (vMin + vMax) / 2
  ore_nec_dif     = dif_km / rata_medie
  ore_nec_pm      = pm_km / rata_medie
  luni_dif        = (ore_nec_dif / ore_an) * 12 * factorC
  luni_pm         = (ore_nec_pm  / ore_an) * 12 * factorC

When nr_echipe == 0 the group has no capacity.  ore_an falls to 0 and
ETA becomes ``float('inf')`` (reported as -1 in JSON) to signal a
blocked / non-achievable state.
"""

from __future__ import annotations

import math

from app.core.validators import clamp_positive, safe_div


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

def nr_echipe(gis: int, rasr: int) -> int:
    """Real team count = min(GIS, RASR).

    Returns 0 when either operand is 0 — the group has no capacity.
    """
    return min(gis, rasr)


def ore_an(ore_sapt: float, sapt_an: int, teams: int, fol: int, pct_fol: float) -> float:
    """Yearly working hours for the group.

    ``ore_an = ore_sapt * sapt_an * (nr_echipe + FOL * pctFOL / 100)``

    Returns 0.0 when *teams* is 0 (blocked group — no capacity).
    """
    if teams <= 0:
        return 0.0
    effective = teams + fol * (pct_fol / 100.0)
    result = ore_sapt * sapt_an * effective
    return clamp_positive(result, fallback=ore_sapt * sapt_an)


def rata_medie(v_min: float, v_max: float) -> float:
    """Average correlation rate = (vMin + vMax) / 2."""
    return clamp_positive((v_min + v_max) / 2.0, fallback=2.25)


def ore_necesare(km: float, rate: float) -> float:
    """Hours required = km / rate.  Returns 0 when rate is non-positive."""
    return safe_div(km, clamp_positive(rate), default=0.0)


_BLOCKED_ETA_INTERNAL: float = float("inf")

# Sentinel used in JSON output: ``-1`` signals a blocked / non-achievable ETA.
BLOCKED_ETA_JSON: float = -1


def _eta_for_json(val: float) -> float:
    """Convert internal ETA to a JSON-safe number.

    ``inf`` (blocked) → ``-1``.
    """
    return BLOCKED_ETA_JSON if not math.isfinite(val) else round(val, 2)


def luni_eta(ore_nec: float, ore_an_val: float, factor_c: float) -> float:
    """ETA in months = (ore_nec / ore_an) * 12 * factorC.

    Returns ``inf`` when *ore_an_val* is 0 and work is pending,
    signalling a blocked / non-achievable state.
    Returns 0 when there is no work to do (ore_nec == 0).
    """
    if ore_an_val <= 0:
        return _BLOCKED_ETA_INTERNAL if ore_nec > 0 else 0.0
    return safe_div(ore_nec, ore_an_val, default=0.0) * 12.0 * max(factor_c, 1.0)


# ---------------------------------------------------------------------------
# High-level compute function called by the API
# ---------------------------------------------------------------------------

def compute_dashboard(payload: dict) -> dict:
    """Compute all dashboard results from a validated payload dict.

    This is the single authoritative source of business calculations.
    """
    from app.core.scenarios import compute_scenarios  # avoid circular at module level

    params = payload.get("params", {})
    groups_in = payload.get("groups", [])

    v_min = clamp_positive(params.get("vMin", 1.5))
    v_max = clamp_positive(params.get("vMax", 3.0))
    ore_sapt = clamp_positive(params.get("oreSapt", 4.0))
    sapt_an = max(1, int(params.get("saptAn", 47)))
    t_dif = clamp_positive(params.get("tDif", 6.0))
    t_pm = clamp_positive(params.get("tPM", 36.0))
    pct_fol = max(0.0, min(params.get("pctFOL", 0.0), 100.0))
    factor_c = max(1.0, params.get("factorC", 1.0))

    avg_rate = rata_medie(v_min, v_max)

    results = []
    for g in groups_in:
        comp = g.get("comp", {})
        gis = max(0, int(comp.get("gis", 1)))
        rasr = max(0, int(comp.get("rasr", 1)))
        fol = max(0, int(comp.get("fol", 0)))

        teams = nr_echipe(gis, rasr)
        oa = ore_an(ore_sapt, sapt_an, teams, fol, pct_fol)

        dif_km = max(0.0, float(g.get("difKm", 0)))
        pm_km = max(0.0, float(g.get("pmKm", 0)))

        o_dif = ore_necesare(dif_km, avg_rate)
        o_pm = ore_necesare(pm_km, avg_rate)

        l_dif = luni_eta(o_dif, oa, factor_c)
        l_pm = luni_eta(o_pm, oa, factor_c)

        blocked = math.isinf(l_dif) or math.isinf(l_pm)

        results.append({
            "name": g.get("name", ""),
            "nr_echipe": teams,
            "ore_an": round(oa, 2),
            "ore_nec_dif": round(o_dif, 2),
            "ore_nec_pm": round(o_pm, 2),
            "luni_dif": _eta_for_json(l_dif),
            "luni_pm": _eta_for_json(l_pm),
            "ok_dif": (not blocked) and l_dif <= t_dif,
            "ok_pm": (not blocked) and l_pm <= t_pm,
        })

    scenarios = compute_scenarios(groups_in, params)

    # Build summary — handle blocked sentinel (-1) safely
    finite_dif = [r["luni_dif"] for r in results if r["luni_dif"] != BLOCKED_ETA_JSON]
    finite_pm = [r["luni_pm"] for r in results if r["luni_pm"] != BLOCKED_ETA_JSON]
    blocked_count = sum(1 for r in results if r["luni_dif"] == BLOCKED_ETA_JSON or r["luni_pm"] == BLOCKED_ETA_JSON)

    summary = {
        "total_dif_km": round(sum(max(0.0, float(g.get("difKm", 0))) for g in groups_in), 4),
        "total_pm_km": round(sum(max(0.0, float(g.get("pmKm", 0))) for g in groups_in), 4),
        "total_groups": len(results),
        "groups_ok_dif": sum(1 for r in results if r["ok_dif"]),
        "groups_ok_pm": sum(1 for r in results if r["ok_pm"]),
        # When any group is blocked, max ETA = -1 (blocked sentinel) because
        # the blocked group dominates the worst-case; finite groups can't offset it.
        "max_luni_dif": BLOCKED_ETA_JSON if blocked_count > 0 else (max(finite_dif) if finite_dif else 0.0),
        "max_luni_pm": BLOCKED_ETA_JSON if blocked_count > 0 else (max(finite_pm) if finite_pm else 0.0),
        "blocked_groups": blocked_count,
        "factor_c": factor_c,
        "rata_medie": round(avg_rate, 4),
    }

    return {
        "rata_medie": round(avg_rate, 4),
        "groups": results,
        "scenarios": scenarios,
        "summary": summary,
    }
