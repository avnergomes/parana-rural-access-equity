"""IBGE data: municipality polygons + urban/rural population from Censo 2022.

Fetches:
    - Malha municipal 2022 for Parana (399 features).
    - SIDRA table 9923 (population by municipio x situacao do domicilio).

Produces a single GeoDataFrame keyed by CD_MUN (7-char string) with
`pop_total`, `pop_urbana`, `pop_rural`, `pct_rural` columns in EPSG:4674.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

from . import config
from .utils import cached_download, first_file, log, unzip


# ---------------------------------------------------------------------------
# 1. Municipality polygons
# ---------------------------------------------------------------------------

def download_municipalities(force: bool = False) -> Path:
    """Fetch the 2022 Parana municipality shapefile ZIP and unzip it.

    Returns the path to the `.shp` file inside the extracted directory.
    """
    zip_path = cached_download(
        config.IBGE_MALHA_MUNICIPAL_PR,
        dest=config.DATA_RAW / "ibge" / "PR_Municipios_2022.zip",
        force=force,
    )
    dest_dir = zip_path.with_suffix("")
    if not dest_dir.exists() or force:
        unzip(zip_path, dest_dir)
    return first_file(dest_dir, [".shp"])


def load_municipalities(force: bool = False) -> gpd.GeoDataFrame:
    """Load the 399 Parana polygons into a normalized GeoDataFrame."""
    shp = download_municipalities(force=force)
    gdf = gpd.read_file(shp, encoding="utf-8")
    # Standardize keys so downstream joins never blow up on stray leading zeros
    # or trimmed strings.
    gdf["CD_MUN"] = gdf["CD_MUN"].astype(str).str.strip().str.zfill(7)
    gdf["NM_MUN"] = gdf["NM_MUN"].astype(str).str.strip()
    # Assert we got exactly Parana.
    if len(gdf) != 399:
        log().warning("expected 399 PR municipios, got %d", len(gdf))
    if gdf.crs is None or gdf.crs.to_epsg() != 4674:
        log().warning("unexpected CRS %s — forcing EPSG:4674", gdf.crs)
        gdf = gdf.set_crs(config.CRS_GEOGRAPHIC, allow_override=True)
    return gdf[["CD_MUN", "NM_MUN", "SIGLA_UF", "AREA_KM2", "geometry"]].copy()


# ---------------------------------------------------------------------------
# 2. SIDRA population table 9923 (Censo 2022, urbana/rural)
# ---------------------------------------------------------------------------

def fetch_sidra_9923(force: bool = False) -> pd.DataFrame:
    """Hit SIDRA and return a wide DataFrame keyed by CD_MUN.

    Columns:
        pop_total, pop_urbana, pop_rural, pct_rural.
    """
    cache = config.DATA_RAW / "ibge" / "sidra_9923_pr.parquet"
    if cache.exists() and not force:
        log().info("cache hit: %s", cache.name)
        return pd.read_parquet(cache)

    log().info("GET %s", config.SIDRA_URL_PR_URBAN_RURAL)
    r = requests.get(config.SIDRA_URL_PR_URBAN_RURAL, timeout=120)
    r.raise_for_status()
    raw = r.json()
    if len(raw) < 2:
        raise RuntimeError("SIDRA returned empty payload — check the endpoint")

    # Row 0 is the header dictionary describing every column; drop it.
    df = pd.DataFrame(raw[1:])
    df["V"] = pd.to_numeric(df["V"], errors="coerce")
    df["CD_MUN"] = df["D1C"].astype(str).str.strip().str.zfill(7)

    # `D4N` is the human-readable name of the situacao do domicilio dimension:
    # "Total" / "Urbana" / "Rural" — pivot on it.
    wide = (
        df.pivot_table(
            index="CD_MUN",
            columns="D4N",
            values="V",
            aggfunc="sum",
        )
        .rename(
            columns={
                "Total": "pop_total",
                "Urbana": "pop_urbana",
                "Rural": "pop_rural",
            }
        )
        .reset_index()
    )
    # SIDRA sometimes labels the total row differently across mirrors — accept
    # both "Total" and no-classification-supplied variants.
    for col in ("pop_total", "pop_urbana", "pop_rural"):
        if col not in wide.columns:
            wide[col] = pd.NA

    wide["pop_total"] = wide["pop_total"].fillna(
        wide[["pop_urbana", "pop_rural"]].sum(axis=1)
    )
    wide["pct_rural"] = wide["pop_rural"] / wide["pop_total"]

    cache.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(cache, index=False)
    log().info("SIDRA 9923 -> %d rows", len(wide))
    return wide


# ---------------------------------------------------------------------------
# 3. Combined: boundaries + population, ready for the spatial join.
# ---------------------------------------------------------------------------

def load_muni_with_population(force: bool = False) -> gpd.GeoDataFrame:
    """One call = 399 Parana polygons carrying Censo 2022 rural population."""
    muni = load_municipalities(force=force)
    pop = fetch_sidra_9923(force=force)
    out = muni.merge(pop, on="CD_MUN", how="left")

    missing = out["pop_total"].isna().sum()
    if missing:
        log().warning(
            "%d municipios missing population — SIDRA join incomplete", missing
        )

    # Persist a canonical processed GeoPackage. This is what every downstream
    # module reads from.
    dest = config.DATA_PROCESSED / "pr_muni_pop2022.gpkg"
    out.to_file(dest, driver="GPKG")
    log().info("saved %d municipios -> %s", len(out), dest.name)
    return out


if __name__ == "__main__":
    gdf = load_muni_with_population()
    print(gdf[["CD_MUN", "NM_MUN", "pop_total", "pop_urbana", "pop_rural"]].head())
    print(
        f"\nParana: {len(gdf)} municipios, "
        f"pop total = {gdf['pop_total'].sum():,.0f}, "
        f"rural = {gdf['pop_rural'].sum():,.0f} "
        f"({gdf['pop_rural'].sum() / gdf['pop_total'].sum():.1%})"
    )
