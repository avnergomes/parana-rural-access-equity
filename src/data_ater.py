"""IDR-Parana ATER (agricultural extension) units.

Source: the official IDR-Parana unit shapefile (`Unidades_IDR_UTM`), which
lists every institute unit as a georeferenced point with its type in the
`UNIDADE` field. The institute separates its network into extension units and
research units; this module keeps only the **extension** ones:

    - "Unidade Municipal de Extensao"  (392, one per served municipio)
    - "Unidade Regional de Extensao"   (22 regional hubs)

and drops research units ("Estacao de Pesquisa", "Polo de Pesquisa") and the
two administrative "Sede" head offices, which do not deliver field extension.

Each unit already carries real LAT/LONG, so no centroid approximation is
needed (unlike the earlier 22-Nucleo seed CSV this replaces). `capacity`
defaults to 1 unit per office.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import geopandas as gpd

from . import config
from .utils import log


def _ensure_shapefile(force: bool = False) -> Path:
    """Unzip the checked-in IDR units archive and return the .shp path."""
    dest_dir = config.DATA_RAW / "idr_units"
    shp = dest_dir / config.IDR_UNITS_SHP_NAME
    if shp.exists() and not force:
        return shp
    if not config.IDR_UNITS_ZIP.exists():
        raise FileNotFoundError(
            f"missing IDR units archive: {config.IDR_UNITS_ZIP}. "
            "It ships with the repo under data/raw/."
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(config.IDR_UNITS_ZIP) as z:
        z.extractall(dest_dir)
    log().info("unzipped %s -> %s", config.IDR_UNITS_ZIP.name, dest_dir)
    return shp


def load_ater_stations(force: bool = False) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame of IDR-PR extension units with capacity + geometry.

    Filtered to extension units only (municipal + regional), reprojected to
    EPSG:4674, `capacity = 1` per unit.
    """
    cache = config.DATA_PROCESSED / "ater_pr_stations.gpkg"
    if cache.exists() and not force:
        log().info("cache hit: %s", cache.name)
        return gpd.read_file(cache)

    shp = _ensure_shapefile(force=force)
    gdf = gpd.read_file(shp)

    # Keep only extension units; drop research units and administrative "Sede".
    unidade = gdf["UNIDADE"].astype(str)
    is_extension = unidade.str.contains("Extens", case=False, na=False)
    ext = gdf[is_extension].copy()
    log().info(
        "IDR units: %d total -> %d extension (%d municipal, %d regional); "
        "dropped %d research/Sede",
        len(gdf),
        len(ext),
        int(unidade[is_extension].str.contains("Municipal", case=False).sum()),
        int(unidade[is_extension].str.contains("Regional", case=False).sum()),
        len(gdf) - len(ext),
    )

    # Normalize to the pipeline CRS and schema.
    ext = ext.to_crs(config.CRS_GEOGRAPHIC)
    ext["CD_MUN"] = ext["Cod_IBGE"].astype(str).str.strip().str.zfill(7)
    ext = ext.rename(columns={"UNIDADE": "unit_type", "REGIONAL": "nucleo_regional"})
    ext["capacity"] = 1.0

    keep = ["CD_MUN", "nucleo_regional", "unit_type", "capacity", "geometry"]
    keep = [c for c in keep if c in ext.columns]
    gdf_out = gpd.GeoDataFrame(ext[keep], geometry="geometry", crs=config.CRS_GEOGRAPHIC)
    gdf_out = gdf_out[gdf_out.geometry.notna()].reset_index(drop=True)

    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf_out.to_file(cache, driver="GPKG")
    log().info("saved %d ATER extension units -> %s", len(gdf_out), cache.name)
    return gdf_out


if __name__ == "__main__":
    gdf = load_ater_stations(force=True)
    print(f"IDR-PR extension units: {len(gdf)}")
    print(gdf[["nucleo_regional", "unit_type", "CD_MUN", "capacity"]].head())
