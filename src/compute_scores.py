"""End-to-end orchestrator: from raw data to a single scored GeoPackage.

Runs:
    1. Load municipality polygons + rural population (IBGE).
    2. Load primary-care facilities (CNES), rural schools (INEP), extension
       stations (IDR-PR ATER).
    3. Compute E2SFCA per service.
    4. Percentile-rank per service, compute equal-weight composite,
       classify into quintiles.
    5. Persist `data/processed/pr_muni_access_scores.gpkg` — the artifact every
       downstream module reads from.

Usage:
    python -m src.compute_scores
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import pandas as pd

from . import config
from .access import score_service
from .data_ater import load_ater_stations
from .data_cnes import load_primary_care_pr
from .data_ibge import load_muni_with_population
from .data_inep import load_rural_schools_pr
from .utils import log


def percentile_rank(series: pd.Series) -> pd.Series:
    """Rank into [0, 100] percentiles. Higher = better access.

    Ties get the average percentile — standard "average" ranking.
    NaNs stay NaN so they don't sneak into the composite.
    """
    return series.rank(pct=True, method="average") * 100.0


def classify_quintiles(series: pd.Series, n: int = config.NUM_QUINTILES) -> pd.Series:
    """Assign 1..n where 1 = worst (bottom quantile), n = best."""
    # `qcut` gives labels 0..n-1 by default; shift so 1 = worst.
    labels = list(range(1, n + 1))
    q = pd.qcut(series.rank(method="first"), q=n, labels=labels)
    return q.astype("Int64")


def build_scores(force: bool = False) -> gpd.GeoDataFrame:
    """Produce the final scored municipio GeoDataFrame."""
    log().info("== compute_scores ==")

    # 1. Base geography + rural population.
    munis = load_muni_with_population(force=force)

    # 2. Supply layers.
    cnes = load_primary_care_pr(force=force)
    inep = load_rural_schools_pr(force=force)
    ater = load_ater_stations(force=force)

    # 3. E2SFCA per service.
    munis["health_e2sfca"] = score_service(
        munis, cnes,
        demand_pop_col="pop_rural",
        supply_cap_col="capacity",
        service_name="health",
    ).astype(float)
    munis["education_e2sfca"] = score_service(
        munis, inep,
        demand_pop_col="pop_rural",
        supply_cap_col="capacity",
        service_name="education",
    ).astype(float)
    munis["extension_e2sfca"] = score_service(
        munis, ater,
        demand_pop_col="pop_rural",
        supply_cap_col="capacity",
        service_name="extension",
    ).astype(float)

    # 4. Percentile ranks per service.
    munis["health_pct"] = percentile_rank(munis["health_e2sfca"])
    munis["education_pct"] = percentile_rank(munis["education_e2sfca"])
    munis["extension_pct"] = percentile_rank(munis["extension_e2sfca"])

    # 5. Composite: equal-weight average of the three percentiles, re-ranked.
    w = config.ACCESS_WEIGHTS
    munis["composite_raw"] = (
        w["health"] * munis["health_pct"]
        + w["education"] * munis["education_pct"]
        + w["extension"] * munis["extension_pct"]
    )
    munis["composite_pct"] = percentile_rank(munis["composite_raw"])

    # 6. Guard: municipios with essentially no rural population should not
    #    dominate the ranking. Mark them but keep them in the file for context.
    munis["is_ranked"] = munis["pop_rural"].fillna(0) >= config.MIN_RURAL_POPULATION

    # 7. Quintiles across ranked municipios only.
    #    Store as float (1.0..5.0, NaN for unranked). GeoPackage/pyogrio coerces
    #    pandas nullable Int64 to *string* on write, which silently breaks every
    #    downstream `quintile == 1` comparison — float round-trips cleanly.
    ranked = munis[munis["is_ranked"]]
    q = classify_quintiles(ranked["composite_pct"])
    munis["quintile"] = pd.NA
    munis.loc[q.index, "quintile"] = q
    munis["quintile"] = pd.to_numeric(munis["quintile"], errors="coerce").astype(float)

    # 8. Underserved flag = bottom quintile among ranked municipios.
    munis["underserved"] = munis["quintile"] == 1

    # 9. Persist.
    dest = config.DATA_PROCESSED / "pr_muni_access_scores.gpkg"
    munis.to_file(dest, driver="GPKG")
    log().info("saved %d scored municipios -> %s", len(munis), dest.name)

    # 10. Print a headline summary — this is what powers the LinkedIn post.
    print_summary(munis)
    return munis


def _raw_access_gap(ranked: gpd.GeoDataFrame, col: str) -> float:
    """Population-weighted ratio of top-quintile vs bottom-quintile raw access.

    Unlike the composite *percentile* gap (which is bounded to 0-100 and so
    compresses), this is computed on the raw E2SFCA score of a single service,
    weighted by rural population. It answers: "how many times more per-capita
    access does the best-served fifth have than the worst-served fifth?"
    """
    top = ranked[ranked["quintile"] == config.NUM_QUINTILES]
    bottom = ranked[ranked["quintile"] == 1]

    def wmean(g: gpd.GeoDataFrame) -> float:
        w = g["pop_rural"].fillna(0).to_numpy(dtype=float)
        v = g[col].fillna(0).to_numpy(dtype=float)
        return float((v * w).sum() / max(w.sum(), 1.0))

    mb = wmean(bottom)
    mt = wmean(top)
    return mt / mb if mb > 0 else float("nan")


def print_summary(gdf: gpd.GeoDataFrame) -> None:
    """Emit the "headline stat" the README uses."""
    ranked = gdf[gdf["is_ranked"]].copy()
    bottom = ranked[ranked["quintile"] == 1]
    top = ranked[ranked["quintile"] == config.NUM_QUINTILES]

    pop_bottom = bottom["pop_rural"].sum()
    pop_ranked = ranked["pop_rural"].sum()
    share = pop_bottom / max(pop_ranked, 1)

    # Percentile-composite gap (bounded metric — reported for completeness but a
    # weak headline: percentiles compress into a narrow band).
    mean_bottom = bottom["composite_raw"].mean()
    mean_top = top["composite_raw"].mean()
    pct_ratio = mean_top / max(mean_bottom, 1e-9)

    # Raw per-service access gaps (the honest, interpretable multiples).
    raw_gaps = {
        svc: _raw_access_gap(ranked, f"{svc}_e2sfca")
        for svc in ("health", "education", "extension")
    }

    log().info("=" * 60)
    log().info(
        "Bottom quintile: %d municipios housing %s of the %s rural residents "
        "(%.1f%% of ranked rural pop).",
        len(bottom),
        f"{pop_bottom:,.0f}",
        f"{pop_ranked:,.0f}",
        100 * share,
    )
    log().info(
        "Composite percentile gap: bottom mean %.1f vs top mean %.1f (%.1fx).",
        mean_bottom, mean_top, pct_ratio,
    )
    log().info(
        "Raw E2SFCA access gap (top vs bottom quintile, pop-weighted): "
        "health %.1fx, education %.1fx, extension %.1fx.",
        raw_gaps["health"], raw_gaps["education"], raw_gaps["extension"],
    )
    log().info("Worst 10 municipios by composite percentile:")
    worst_10 = ranked.nsmallest(10, "composite_pct")[
        ["NM_MUN", "pop_rural", "composite_pct"]
    ]
    for _, row in worst_10.iterrows():
        log().info("  %-30s pop_rural=%7.0f  composite_pct=%.1f",
                   row["NM_MUN"], row["pop_rural"], row["composite_pct"])
    log().info("=" * 60)

    # Persist headline stats JSON — read by the LinkedIn draft template.
    import json
    stats = {
        "bottom_quintile_muni_count": int(len(bottom)),
        "bottom_quintile_pop_rural": int(pop_bottom),
        "ranked_pop_rural": int(pop_ranked),
        "bottom_quintile_pop_share": float(share),
        "composite_percentile_gap_ratio": float(pct_ratio),
        "raw_access_gap_health": float(raw_gaps["health"]),
        "raw_access_gap_education": float(raw_gaps["education"]),
        "raw_access_gap_extension": float(raw_gaps["extension"]),
        "worst_10_municipios": worst_10.assign(
            NM_MUN=worst_10["NM_MUN"].astype(str)
        ).to_dict(orient="records"),
        "params": {
            "beta_km": config.E2SFCA_BETA_KM,
            "d0_km": config.E2SFCA_D0_KM,
            "weights": config.ACCESS_WEIGHTS,
            "min_rural_population": config.MIN_RURAL_POPULATION,
            "num_quintiles": config.NUM_QUINTILES,
        },
    }
    dest = config.OUTPUT_DIR / "headline_stats.json"
    dest.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    log().info("wrote headline stats -> %s", dest.name)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download raw data")
    args = ap.parse_args()
    build_scores(force=args.force)


if __name__ == "__main__":
    main()
