def ore_an(params, comp):
    teams = min(comp.get("gis",1), comp.get("rasr",1))
    fol = comp.get("fol",0) * (params.get("pctFOL",0)/100)
    return params["oreSapt"] * params["saptAn"] * (teams + fol)


def compute_eta(km, rate, ore_an_val, factor):
    if ore_an_val <= 0:
        return float("inf")
    return (km / rate) / ore_an_val * factor


def compute_dashboard(payload: dict):
    params = payload.get("params", {})
    groups = payload.get("groups", [])

    results = []

    for g in groups:
        comp = g.get("comp", {"gis":1,"rasr":1,"fol":0})
        oa = ore_an(params, comp)
        eta = compute_eta(g.get("difKm",0), params.get("vMed",2.25), oa, params.get("factorC",1))

        results.append({
            "name": g.get("name"),
            "oreAn": oa,
            "etaYears": eta
        })

    return {"results": results}
