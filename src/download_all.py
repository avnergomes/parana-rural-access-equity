"""Fetch every raw dataset the pipeline needs.

Idempotent: cached files are reused. Pass --force to re-download.

Order:
    1. IBGE municipality shapefile (~4 MB).
    2. IBGE SIDRA 9923 (Censo 2022 urbano/rural — ~40 KB JSON).
    3. CNES ST (competencia yyyymm — ~1.5 MB DBC via PySUS).
    4. INEP Censo Escolar ZIP (~500 MB — dominates the download budget).
    5. ATER stations (either user-provided CSV or the checked-in seed).
"""

from __future__ import annotations

import argparse
import sys

from . import config
from .data_ater import load_ater_stations
from .data_cnes import load_primary_care_pr
from .data_ibge import load_muni_with_population
from .data_inep import load_rural_schools_pr
from .utils import log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download all sources")
    ap.add_argument(
        "--skip-inep",
        action="store_true",
        help="skip the 500 MB INEP download (useful during dev)",
    )
    args = ap.parse_args()

    log().info("== download_all ==")
    log().info("raw data cache: %s", config.DATA_RAW)

    log().info("[1/4] IBGE municipality polygons + Censo 2022 population")
    load_muni_with_population(force=args.force)

    log().info(
        "[2/4] CNES primary-care facilities (competencia %d-%02d)",
        config.CNES_COMPETENCIA_YEAR,
        config.CNES_COMPETENCIA_MONTH,
    )
    load_primary_care_pr(force=args.force)

    if not args.skip_inep:
        log().info("[3/4] INEP Censo Escolar %d rural schools", config.INEP_CENSO_ESCOLAR_YEAR)
        load_rural_schools_pr(force=args.force)
    else:
        log().info("[3/4] INEP download skipped (--skip-inep)")

    log().info("[4/4] IDR-Parana ATER stations")
    load_ater_stations(force=args.force)

    log().info("== done ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
