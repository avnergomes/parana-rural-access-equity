"""Paraná Rural Access Equity — pipeline package.

Modules:
    config: URLs, CRS, constants, thresholds.
    utils: cached downloads (OS-trust-store TLS), unzip, logging helpers.
    data_ibge: municipality boundaries + Censo 2022 rural population.
    data_cnes: primary-care health facilities (UBS) in PR via open-data API.
    data_inep: rural schools in PR (TP_LOCALIZACAO=2), Censo Escolar 2024.
    data_ater: IDR-Paraná extension offices (22 Núcleos Regionais).
    access: Enhanced 2-Step Floating Catchment Area implementation.
    compute_scores: composite access index per municipality.
    render_outputs: static PNG choropleth + interactive Folium HTML.
    download_all: orchestrator that runs every download step in order.
"""

__version__ = "0.1.0"
