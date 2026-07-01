"""IDR-Parana ATER (agricultural extension) stations.

There is no fully-public API listing IDR-PR regional and municipal offices,
so this module works from a hand-curated CSV of the 22 Nucleos Regionais.

Lookup order:
    1. `data/raw/ater_pr_stations.csv` — user-provided (overrides).
    2. `data/raw/ater_pr_stations_seed.csv` — the checked-in fallback covering
       the 22 Nucleos Regionais by seat city.

The `capacity` column defaults to 1 unit per station. Downstream E2SFCA will
weight rural population against station count.

Coordinates are resolved by joining CD_MUN to the IBGE municipality polygon
and using its geometric centroid — a defensible approximation for a Nucleo
that serves its whole seat municipio.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from . import config
from .data_ibge import load_municipalities
from .utils import log


ATER_USER_CSV = config.DATA_RAW / "ater_pr_stations.csv"
ATER_SEED_CSV = config.DATA_RAW / "ater_pr_stations_seed.csv"


def _pick_source() -> Path:
    """Prefer the user-provided CSV; fall back to the seed."""
    if ATER_USER_CSV.exists():
        log().info("using user-provided ATER stations: %s", ATER_USER_CSV.name)
        return ATER_USER_CSV
    if ATER_SEED_CSV.exists():
        log().info("using seed ATER stations: %s", ATER_SEED_CSV.name)
        return ATER_SEED_CSV
    raise FileNotFoundError(
        f"no ATER CSV found — expected {ATER_USER_CSV} or {ATER_SEED_CSV}"
    )


def load_ater_stations(force: bool = False) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame of IDR-PR extension stations with capacity + geometry."""
    cache = config.DATA_PROCESSED / "ater_pr_stations.gpkg"
    if cache.exists() and not force:
        log().info("cache hit: %s", cache.name)
        return gpd.read_file(cache)

    src = _pick_source()
    df = pd.read_csv(src, dtype={"CD_MUN": str})
    df["CD_MUN"] = df["CD_MUN"].str.strip().str.zfill(7)
    if "capacity" not in df.columns:
        df["capacity"] = 1.0

    munis = load_municipalities(force=False)
    # Reproject once to a metric CRS so centroid() is meaningful.
    munis_metric = munis.to_crs(config.CRS_METRIC_PR)
    centroids = (
        munis_metric.assign(geometry=munis_metric.geometry.centroid)
        .to_crs(config.CRS_GEOGRAPHIC)[["CD_MUN", "NM_MUN", "geometry"]]
    )

    joined = df.merge(centroids, on="CD_MUN", how="left", suffixes=("", "_muni"))
    missing = joined["geometry"].isna().sum()
    if missing:
        log().warning("%d ATER stations have no matching CD_MUN centroid", missing)

    gdf = gpd.GeoDataFrame(joined, geometry="geometry", crs=config.CRS_GEOGRAPHIC)
    gdf = gdf.dropna(subset=["geometry"]).reset_index(drop=True)

    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache, driver="GPKG")
    log().info("saved %d ATER stations -> %s", len(gdf), cache.name)
    return gdf


if __name__ == "__main__":
    gdf = load_ater_stations()
    print(f"IDR-PR extension stations: {len(gdf)}")
    print(gdf[["nucleo_regional", "NM_MUN", "capacity"]].head())
