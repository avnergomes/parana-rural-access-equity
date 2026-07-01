"""INEP data: rural schools in Parana (Censo Escolar microdata).

Downloads the national Censo Escolar ZIP (~30 MB compressed; the school CSV is
~217 MB uncompressed) once, then reads only the school table filtered to PR
with `TP_LOCALIZACAO == 2` (rural) or a nonzero `TP_LOCALIZACAO_DIFERENCIADA`
(quilombola / assentamento / floresta / ...).

Georeferencing note (verified 2026-07-01): the Censo Escolar **2024** microdata
no longer ships LATITUDE / LONGITUDE columns (INEP dropped point coordinates
from the public microdata). We therefore geocode each school to the centroid of
its CO_MUNICIPIO polygon. This matches the municipal resolution of the whole
analysis and is consistent with the ATER layer, which is also centroid-based.
A future v2 can swap in the INEP "Catalogo de Escolas" georef for true points.

Produces a GeoDataFrame of active rural school points in EPSG:4674 with a
`capacity` column = `QT_MAT_BAS` (total enrolments — a natural E2SFCA weight).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from . import config
from .data_ibge import load_municipalities
from .utils import cached_download, log


# INEP microdata is semicolon-delimited, latin-1, decimal comma.
INEP_CSV_SEP = ";"

# Columns pulled from the raw CSV. Extras (infra flags) enable a follow-up
# "quality-of-service" enrichment without another download.
INEP_USE_COLS = [
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "SG_UF",
    "CO_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    "TP_LOCALIZACAO_DIFERENCIADA",
    "TP_SITUACAO_FUNCIONAMENTO",
    "QT_MAT_BAS",
    "IN_INTERNET",
    "IN_AGUA_POTAVEL",
    "IN_ESGOTO_REDE_PUBLICA",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
]


# ---------------------------------------------------------------------------
# 1. Download + locate the schools CSV inside the ZIP.
# ---------------------------------------------------------------------------

def download_zip(force: bool = False) -> Path:
    """Fetch the Censo Escolar ZIP (~30 MB) with retry + caching."""
    dest = config.DATA_RAW / "inep" / f"microdados_censo_escolar_{config.INEP_CENSO_ESCOLAR_YEAR}.zip"
    return cached_download(config.INEP_CENSO_ESCOLAR_ZIP, dest=dest, force=force, timeout=300)


def _pick_escolas_csv(zip_path: Path) -> str:
    """Find the ed_basica CSV inside the ZIP without full extraction."""
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            low = name.lower()
            if low.endswith(".csv") and config.INEP_ZIP_ESCOLAS_HINT in low:
                return name
    raise FileNotFoundError(
        f"could not find a CSV containing '{config.INEP_ZIP_ESCOLAS_HINT}' in {zip_path}"
    )


# ---------------------------------------------------------------------------
# 2. Load + filter.
# ---------------------------------------------------------------------------

def _load_raw(zip_path: Path) -> pd.DataFrame:
    """Read the school CSV directly out of the ZIP (no disk extraction)."""
    csv_name = _pick_escolas_csv(zip_path)
    log().info("reading %s from %s", csv_name, zip_path.name)
    with zipfile.ZipFile(zip_path) as z, z.open(csv_name) as fh:
        df = pd.read_csv(
            fh,
            sep=INEP_CSV_SEP,
            encoding="latin-1",
            decimal=",",
            usecols=[c for c in INEP_USE_COLS if c],
            dtype={"CO_ENTIDADE": "int64", "CO_MUNICIPIO": "int64"},
            low_memory=False,
        )
    log().info("INEP raw rows: %d", len(df))
    return df


def _filter_pr_rural(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to active Parana rural (or "diferenciada") schools."""
    m = (
        (df["SG_UF"] == config.UF_ABBR_PR)
        & (df["TP_SITUACAO_FUNCIONAMENTO"] == 1)
        & (
            (df["TP_LOCALIZACAO"] == config.INEP_TP_LOCALIZACAO_RURAL)
            | (df["TP_LOCALIZACAO_DIFERENCIADA"].fillna(0) > 0)
        )
    )
    kept = df[m].copy()
    log().info(
        "INEP filter: %d PR rural (+ diferenciada) active schools from %d nation-wide",
        len(kept),
        len(df),
    )
    return kept


# ---------------------------------------------------------------------------
# 3. Geocode to municipality centroid.
# ---------------------------------------------------------------------------

def _attach_centroids(df: pd.DataFrame, force: bool = False) -> gpd.GeoDataFrame:
    """Place each school at the centroid of its CO_MUNICIPIO polygon.

    The 2024 microdata carries no coordinates, so the municipal centroid is the
    best available anchor. Distances are computed in the metric CRS to avoid the
    geographic-centroid warning, then reprojected back to EPSG:4674.
    """
    muni = load_municipalities(force=force)[["CD_MUN", "geometry"]].copy()
    cents = muni.to_crs(config.CRS_METRIC_PR)
    cents["geometry"] = cents.geometry.centroid
    cents = cents.to_crs(config.CRS_GEOGRAPHIC)
    cent_by_mun = dict(zip(cents["CD_MUN"], cents.geometry))

    df = df.copy()
    df["CD_MUN"] = df["CO_MUNICIPIO"].astype(str).str.strip().str.zfill(7)
    df["geometry"] = df["CD_MUN"].map(cent_by_mun)

    missing = df["geometry"].isna().sum()
    if missing:
        log().warning("%d schools have no matching municipal centroid — dropped", missing)
        df = df[df["geometry"].notna()].copy()

    return gpd.GeoDataFrame(df, geometry="geometry", crs=config.CRS_GEOGRAPHIC)


# ---------------------------------------------------------------------------
# 4. Public entrypoint.
# ---------------------------------------------------------------------------

def load_rural_schools_pr(force: bool = False) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame of active rural PR schools with capacity.

    Each school is anchored at its municipality centroid (see module docstring)
    and weighted by QT_MAT_BAS (basic-education enrolment).
    """
    cache = config.DATA_PROCESSED / f"inep_pr_rural_{config.INEP_CENSO_ESCOLAR_YEAR}.gpkg"
    if cache.exists() and not force:
        log().info("cache hit: %s", cache.name)
        return gpd.read_file(cache)

    zip_path = download_zip(force=force)
    df = _load_raw(zip_path)
    df = _filter_pr_rural(df)

    # Capacity for E2SFCA: enrolments if present, else a small floor so schools
    # with missing counts still participate.
    df["capacity"] = pd.to_numeric(df["QT_MAT_BAS"], errors="coerce").fillna(10).clip(lower=1)

    gdf = _attach_centroids(df, force=force)

    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache, driver="GPKG")
    log().info("saved %d rural schools -> %s", len(gdf), cache.name)
    return gdf


if __name__ == "__main__":
    gdf = load_rural_schools_pr()
    print(f"Rural + diferenciada PR schools ({config.INEP_CENSO_ESCOLAR_YEAR}): {len(gdf)}")
    print(gdf[["CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO", "TP_LOCALIZACAO"]].head())
