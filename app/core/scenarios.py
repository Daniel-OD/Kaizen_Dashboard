"""Reusable scenario calculations (worst / medium / best)."""

from __future__ import annotations

from app.core.calculations import nr_echipe, ore_an, ore_necesare, luni_eta
from app.core.validators import clamp_positive


def _max_eta(groups: list[dict], params: dict, rate: float) -> tuple[float, float]:
    """Return (max_luni_dif, max_luni_pm) across *groups* at the given *rate*."""
    ore_sapt = clamp_positive(params.get("oreSapt", 4.0))
    sapt_an_val = max(1, int(params.get("saptAn", 47)))
    pct_fol = max(0.0, min(params.get("pctFOL", 0.0), 100.0))
    factor_c = max(1.0, params.get("factorC", 1.0))

    max_dif: float = 0.0
    max_pm: float = 0.0

    for g in groups:
        comp = g.get("comp", {})
        teams = nr_echipe(
            max(0, int(comp.get("gis", 1))),
            max(0, int(comp.get("rasr", 1))),
        )
        fol = max(0, int(comp.get("fol", 0)))
        oa = ore_an(ore_sapt, sapt_an_val, teams, fol, pct_fol)

        dif_km = max(0.0, float(g.get("difKm", 0)))
        pm_km = max(0.0, float(g.get("pmKm", 0)))

        l_dif = luni_eta(ore_necesare(dif_km, rate), oa, factor_c)
        l_pm = luni_eta(ore_necesare(pm_km, rate), oa, factor_c)

        if l_dif > max_dif:
            max_dif = l_dif
        if l_pm > max_pm:
            max_pm = l_pm

    return max_dif, max_pm


def compute_scenarios(groups: list[dict], params: dict) -> list[dict]:
    """Compute worst / medium / best scenario ETAs."""
    v_min = clamp_positive(params.get("vMin", 1.5))
    v_max = clamp_positive(params.get("vMax", 3.0))
    v_med = (v_min + v_max) / 2.0

    out: list[dict] = []
    for label_rate in [(v_min, "worst"), (v_med, "medium"), (v_max, "best")]:
        rate = label_rate[0]
        dif_m, pm_m = _max_eta(groups, params, rate)
        out.append({
            "rate": round(rate, 4),
            "max_eta_dif_years": round(dif_m / 12.0, 4),
            "max_eta_pm_years": round(pm_m / 12.0, 4),
        })
    return out
