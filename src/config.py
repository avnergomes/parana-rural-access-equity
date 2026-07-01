"""Static configuration: URLs, codes, CRS choices, thresholds.

Everything that could change if IBGE / DATASUS / Geofabrik rearrange their
portals lives here. When something 404s, this is the file to edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_RAW: Path = REPO_ROOT / "data" / "raw"
DATA_PROCESSED: Path = REPO_ROOT / "data" / "processed"
OUTPUT_DIR: Path = REPO_ROOT / "output"
FIGURES_DIR: Path = OUTPUT_DIR / "figures"

for _p in (DATA_RAW, DATA_PROCESSED, OUTPUT_DIR, FIGURES_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Geographic constants
# ---------------------------------------------------------------------------

UF_CODE_PR: int = 41
UF_ABBR_PR: str = "PR"

# SIRGAS 2000 (Brazilian official geographic CRS) for storage and joins.
CRS_GEOGRAPHIC: str = "EPSG:4674"
# UTM 22S (covers most of Parana) for metric operations (distances, areas).
CRS_METRIC_PR: str = "EPSG:31982"
# Web Mercator for Folium/Leaflet display.
CRS_WEB: str = "EPSG:3857"

# ---------------------------------------------------------------------------
# IBGE — municipality boundaries + Censo 2022
# ---------------------------------------------------------------------------

# Malha municipal 2022 — shapefile per UF.
# Primary IBGE geoftp (public open FTP served over HTTPS).
IBGE_MALHA_MUNICIPAL_PR: str = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2022/UFs/PR/PR_Municipios_2022.zip"
)

# SIDRA REST API base for programmatic table pulls.
# Table 4709: Populacao residente por situacao do domicilio (Censo 2010, legacy).
# Table 4714: Populacao residente por sexo e idade (Censo 2022, latest).
# Table 9605: Populacao residente por situacao do domicilio (Censo 2022) — key for rural/urban split.
SIDRA_BASE: str = "https://apisidra.ibge.gov.br/values"
# Table 9923: Populacao residente por situacao do domicilio (Censo 2022).
# Verified 2026-07-01. This is the correct table — the older 4709/4710 do NOT
# carry 2022 data. Full endpoint fetches "all municipios in UF=41 x Censo 2022 x
# variable=93 (populacao) x classification c1 (Total/Urbana/Rural)".
SIDRA_TABLE_CENSO2022_URBAN_RURAL: int = 9923
SIDRA_URL_PR_URBAN_RURAL: str = (
    "https://apisidra.ibge.gov.br/values"
    "/t/9923/n6/in%20n3%2041/v/93/p/2022/c1/all"
)
# Companion table: total population 2022 per municipality (sanity check).
SIDRA_TABLE_CENSO2022_TOTAL: int = 9514

# ---------------------------------------------------------------------------
# CNES — health facilities
# ---------------------------------------------------------------------------

# CNES facility "tipos" — codes that correspond to Atencao Basica / primary care.
# Reference: https://wiki.saude.gov.br/cnes/index.php/Categoria:Principais_d%C3%BAvidas_Nova_Classifica%C3%A7%C3%A3o_de_Tipos_de_Estabelecimento
# NB: apidadosabertos.saude.gov.br returns codigo_tipo_unidade as int, so we
# store the integer form here. The legacy DBC layout used zero-padded strings.
CNES_TIPO_PRIMARY_CARE: tuple[int, ...] = (
    1,   # POSTO DE SAUDE
    2,   # CENTRO DE SAUDE / UNIDADE BASICA (UBS)
    32,  # UNIDADE MOVEL FLUVIAL
    40,  # UNIDADE MOVEL TERRESTRE (medico/odontologico)
)

# Snapshot label — used only for cache filenames now that we hit the live API.
CNES_COMPETENCIA_YEAR: int = 2026
CNES_COMPETENCIA_MONTH: int = 5

# Ministério da Saúde public "dados abertos" REST API. Live, no auth.
# Verified 2026-07-01: server-side filter by codigo_uf + codigo_tipo_unidade
# works, offset pagination works, fixed page size = 20.
CNES_API_BASE: str = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
CNES_API_PAGE_SIZE: int = 20

# Legacy DBC path (DATASUS FTP) — kept as documented fallback. FTP host was
# unreachable from many networks in mid-2026, which is why the pipeline pivoted
# to the API. Re-enable via `--use-ftp` in data_cnes.py if the API is down.
CNES_FTP_HOST: str = "ftp.datasus.gov.br"
CNES_FTP_PATH_ST: str = "/dissemin/publicos/CNES/200508_/Dados/ST"
CNES_FTP_FILE_TEMPLATE: str = "STPR{yy:02d}{mm:02d}.dbc"

# ---------------------------------------------------------------------------
# INEP — schools
# ---------------------------------------------------------------------------

# Censo Escolar microdata ZIP. Verified 2026-07-01 (2024 fully consolidated;
# 2025 is preliminary — stick with 2024 for the paper).
INEP_CENSO_ESCOLAR_YEAR: int = 2024
INEP_CENSO_ESCOLAR_ZIP: str = (
    "https://download.inep.gov.br/dados_abertos/"
    "microdados_censo_escolar_2024.zip"
)
# Fallback mirror if inep.gov.br is down:
INEP_CENSO_ESCOLAR_MIRROR: str = (
    "https://basedosdados.org/dataset/dae21af4-4b6a-42f4-b94a-4c2061ea9de5"
)

# Inside the ZIP, the schools CSV is at:
INEP_ZIP_ESCOLAS_HINT: str = "microdados_ed_basica_"  # matches ...2024.csv

# TP_LOCALIZACAO codes (INEP schema, stable across years):
INEP_TP_LOCALIZACAO_URBANA: int = 1
INEP_TP_LOCALIZACAO_RURAL: int = 2

# TP_DEPENDENCIA — schools we care about for public rural access:
# 1=Federal, 2=Estadual, 3=Municipal, 4=Privada
INEP_TP_DEPENDENCIA_PUBLIC: tuple[int, ...] = (1, 2, 3)

# Parana bounding box (WGS84, generous) — drops obviously broken lat/lon.
PR_BBOX_LON_MIN: float = -54.7
PR_BBOX_LON_MAX: float = -48.0
PR_BBOX_LAT_MIN: float = -26.8
PR_BBOX_LAT_MAX: float = -22.4

# ---------------------------------------------------------------------------
# OpenStreetMap — via Geofabrik
# ---------------------------------------------------------------------------

# Sul region (PR + SC + RS) — smallest extract that fully contains Parana.
GEOFABRIK_SUL_PBF: str = (
    "https://download.geofabrik.de/south-america/brazil/sul-latest.osm.pbf"
)

# Highway classes to keep for drive-time isochrones.
# Bike/foot networks would filter to a different set.
OSM_HIGHWAY_DRIVE: tuple[str, ...] = (
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "unclassified", "residential",
    "service",  # keep for reaching facility entrances
)

# Assumed rural driving speed (km/h) per class when maxspeed is missing.
# Conservative — favors reachability rather than optimistic ETA.
OSM_SPEED_KMH: dict[str, float] = {
    "motorway": 100, "motorway_link": 60,
    "trunk": 80, "trunk_link": 50,
    "primary": 70, "primary_link": 40,
    "secondary": 60, "secondary_link": 35,
    "tertiary": 50, "tertiary_link": 30,
    "unclassified": 40,
    "residential": 30,
    "service": 20,
}

# Isochrone budget for the access catchment (minutes of drive time).
# 30 min is the standard "practical rural service reach" in Brazilian literature.
ISOCHRONE_MINUTES: int = 30

# ---------------------------------------------------------------------------
# Scoring / weighting
# ---------------------------------------------------------------------------

# --- Enhanced 2SFCA (Luo & Qi 2009) parameters -----------------------------
# Gaussian distance decay W(d) = exp(-d^2 / beta^2)
# beta = 30 km matches the Luo & Qi calibration and Brazilian rural health-
# geography literature (see docs/references.bib).
E2SFCA_BETA_KM: float = 30.0
# Catchment cutoff distance (km). Facilities beyond d0 don't count.
E2SFCA_D0_KM: float = 50.0

# --- Composite index weights ------------------------------------------------
# Equal 1/3 across health, education, extension. Sensitivity checks (PCA and
# health-heavy 0.5/0.25/0.25) are computed as a robustness table in the notebook.
ACCESS_WEIGHTS: dict[str, float] = {
    "health": 1.0 / 3.0,
    "education": 1.0 / 3.0,
    "extension": 1.0 / 3.0,
}

# --- Ranking framing --------------------------------------------------------
# Bottom-quintile threshold (0.20) for the "underserved" flag.
UNDERSERVED_QUANTILE: float = 0.20
NUM_QUINTILES: int = 5

# Minimum rural population to include a municipio in the ranking.
# Filters out fully-urban capitals whose rural counts approach zero.
MIN_RURAL_POPULATION: int = 500

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunConfig:
    """Per-run switches. Instantiate in scripts to keep behavior explicit."""

    verbose: bool = True
    force_redownload: bool = False
    isochrone_minutes: int = ISOCHRONE_MINUTES
    underserved_quantile: float = UNDERSERVED_QUANTILE
    min_rural_population: int = MIN_RURAL_POPULATION


DEFAULT_RUN = RunConfig()
