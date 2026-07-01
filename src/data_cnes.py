"""CNES data: primary-care health facilities in Parana.

Primary path (2026 onward): live REST API at apidadosabertos.saude.gov.br —
public, no auth, updated monthly. Fixed 20 records per page, server-side
filter by codigo_uf + codigo_tipo_unidade.

Legacy path (DATASUS FTP + PySUS): kept for reference. FTP was unreachable
from many networks in mid-2026 due to backend issues; PySUS 2.4 additionally
had a Windows-path bug in its Hetzner catalog URL. Both paths remain wired so
future runs can swap back if the API changes.

Produces a GeoDataFrame of primary-care points in EPSG:4674 with a
`capacity` column (default 1.0 per facility).
"""

from __future__ import annotations

import time

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

from . import config
from .utils import log


# Columns the API returns that we care about. Everything else is dropped.
_API_KEEP_COLS = {
    "codigo_cnes": "CNES",
    "codigo_municipio": "CODUFMUN",
    "codigo_tipo_unidade": "TP_UNID",
    "descricao_esfera_administrativa": "GESTAO",
    "descricao_natureza_juridica_estabelecimento": "NAT_JUR",
    "latitude_estabelecimento_decimo_grau": "LATITUDE",
    "longitude_estabelecimento_decimo_grau": "LONGITUDE",
    "nome_fantasia": "NOMEFAN",
    "codigo_cep_estabelecimento": "COD_CEP",
}


# ---------------------------------------------------------------------------
# 1. Live REST API path (primary)
# ---------------------------------------------------------------------------

def _fetch_tipo_via_api(
    tipo: int,
    uf_code: int = config.UF_CODE_PR,
    page_size: int = config.CNES_API_PAGE_SIZE,
    sleep_between: float = 0.05,
) -> list[dict]:
    """Paginate all rows for a given codigo_tipo_unidade + codigo_uf."""
    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "codigo_uf": uf_code,
            "codigo_tipo_unidade": tipo,
            "limit": page_size,
            "offset": offset,
        }
        page: list[dict] = []
        for attempt in range(1, 4):
            try:
                r = requests.get(config.CNES_API_BASE, params=params, timeout=60)
                r.raise_for_status()
                page = r.json().get("estabelecimentos", [])
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 3:
                    raise
                log().warning(
                    "CNES API tipo=%d offset=%d failed (%s) — retry %d/3",
                    tipo, offset, exc, attempt,
                )
                time.sleep(2)
        if not page:
            break
        rows.extend(page)
        offset += page_size
        if len(page) < page_size:
            break
        time.sleep(sleep_between)
    log().info("CNES API tipo=%d -> %d rows", tipo, len(rows))
    return rows


def _fetch_via_api() -> pd.DataFrame:
    """Sweep every primary-care tipo and merge into one DataFrame."""
    all_rows: list[dict] = []
    for tipo in config.CNES_TIPO_PRIMARY_CARE:
        all_rows.extend(_fetch_tipo_via_api(tipo))
    if not all_rows:
        raise RuntimeError("CNES API returned zero rows — check filters / network")
    df = pd.DataFrame(all_rows)
    # Keep only the columns we use downstream, renamed to match the legacy DBC
    # layout so the rest of the pipeline stays identical.
    keep = [c for c in _API_KEEP_COLS if c in df.columns]
    df = df[keep].rename(columns=_API_KEEP_COLS)
    log().info("CNES API total rows across all primary-care tipos: %d", len(df))
    return df


# ---------------------------------------------------------------------------
# 2. Legacy DBC path (FTP + pyreaddbc) — kept for future use
# ---------------------------------------------------------------------------

def _fetch_via_ftp(year: int, month: int) -> pd.DataFrame:
    """Direct DATASUS FTP + local DBC decode. Used only when the API is down.

    NB: as of 2026-07 the DATASUS FTP host was unreachable from many
    networks. The API path above is the primary route now.
    """
    from .utils import cached_download

    yy = year % 100
    fname = config.CNES_FTP_FILE_TEMPLATE.format(yy=yy, mm=month)
    url = f"https://{config.CNES_FTP_HOST}{config.CNES_FTP_PATH_ST}/{fname}"
    dest = config.DATA_RAW / "cnes" / fname
    cached_download(url, dest=dest)

    from pyreaddbc import read_dbc

    df = read_dbc(str(dest), encoding="latin-1")
    log().info("FTP+pyreaddbc returned %d CNES rows from %s", len(df), fname)
    # Legacy DBC uses zero-padded strings; normalize to int to match the API path.
    if "TP_UNID" in df.columns:
        df["TP_UNID"] = pd.to_numeric(df["TP_UNID"], errors="coerce").astype("Int64")
    return df


# ---------------------------------------------------------------------------
# 3. Normalization and filtering
# ---------------------------------------------------------------------------

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Trim, type-cast, and drop rows that cannot possibly geolocate."""
    df = df.copy()
    df["TP_UNID"] = pd.to_numeric(df["TP_UNID"], errors="coerce").astype("Int64")
    df["CODUFMUN"] = df["CODUFMUN"].astype(str).str.strip().str.zfill(6)
    for col in ("LATITUDE", "LONGITUDE"):
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .replace({"": None, "nan": None, "None": None})
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _filter_primary_care_pr(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only Parana primary-care facilities with valid coordinates."""
    is_pr = df["CODUFMUN"].str.startswith(str(config.UF_CODE_PR))
    is_primary = df["TP_UNID"].isin(config.CNES_TIPO_PRIMARY_CARE)
    lat_ok = df["LATITUDE"].between(config.PR_BBOX_LAT_MIN, config.PR_BBOX_LAT_MAX)
    lon_ok = df["LONGITUDE"].between(config.PR_BBOX_LON_MIN, config.PR_BBOX_LON_MAX)
    mask = is_pr & is_primary & lat_ok & lon_ok
    kept = df[mask].copy()
    log().info(
        "CNES filter: %d/%d rows kept (PR primary-care with valid georef)",
        len(kept),
        len(df),
    )
    return kept


# ---------------------------------------------------------------------------
# 4. Public entrypoint
# ---------------------------------------------------------------------------

def load_primary_care_pr(
    year: int | None = None,
    month: int | None = None,
    force: bool = False,
    use_ftp: bool = False,
) -> gpd.GeoDataFrame:
    """One call = every PR primary-care CNES facility, ready for spatial join."""
    year = year or config.CNES_COMPETENCIA_YEAR
    month = month or config.CNES_COMPETENCIA_MONTH

    cache = config.DATA_PROCESSED / f"cnes_pr_primary_{year}{month:02d}.gpkg"
    if cache.exists() and not force:
        log().info("cache hit: %s", cache.name)
        return gpd.read_file(cache)

    if use_ftp:
        df = _fetch_via_ftp(year, month)
    else:
        try:
            df = _fetch_via_api()
        except Exception as exc:  # noqa: BLE001
            log().warning("API path failed (%s) — falling back to FTP", exc)
            df = _fetch_via_ftp(year, month)

    df = _clean(df)
    df = _filter_primary_care_pr(df)

    # Every facility has a capacity of 1 for E2SFCA (units count, not staff).
    # Downstream can swap this for a richer capacity signal if needed.
    df["capacity"] = 1.0

    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["LONGITUDE"], df["LATITUDE"])],
        crs=config.CRS_GEOGRAPHIC,
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache, driver="GPKG")
    log().info("saved %d primary-care facilities -> %s", len(gdf), cache.name)
    return gdf


if __name__ == "__main__":
    gdf = load_primary_care_pr()
    print(f"Primary-care CNES facilities in Parana ({config.CNES_COMPETENCIA_YEAR}-"
          f"{config.CNES_COMPETENCIA_MONTH:02d}): {len(gdf)}")
    print(gdf[["CNES", "NOMEFAN", "CODUFMUN", "TP_UNID"]].head())
