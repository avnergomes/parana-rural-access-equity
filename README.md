# Paraná Rural Access Equity

**Which of Paraná's 399 municipalities are underserved by rural health, education, and agricultural extension services relative to their rural population?**

A reproducible spatial equity analysis using open data (IBGE, CNES, INEP, IDR-Paraná) and open tools (Python, GeoPandas, Folium, Matplotlib).

**Live map:** _(will point to `avnergomes.github.io/parana-rural-access-equity` once deployed)_

**Portfolio context:** built as a public-data adaptation of Project 1 from [GEO CAREERS' April 2026 portfolio guide](https://www.geo-careers.com/posts/gis-portfolio-guide/) (skill cluster: Python + GeoPandas, target salary band US$135K), reframed around Paraná's 399 municipalities and Brazilian federal open data.

---

## Quick answer

> **73 of Paraná's municipalities (the bottom quintile of 364 ranked) house about 1 in 6 of the state's rural residents, 196,356 people, with the weakest combined access to primary care, rural schools, and agricultural extension.** In that worst-served fifth, per-capita access to primary care and rural schooling runs roughly 2.2 to 2.3 times below the best-served fifth.

They cluster in the Centro-Sul and Campos Gerais interior (Tibagi, Candói, Altamira do Paraná), the Norte Pioneiro border, and small Costa Oeste municipios on the Itaipu reservoir.

Bottom quintile choropleth: see `output/choropleth_access_score.png` and `output/interactive_map.html`.

---

## How to reproduce

Requires Python 3.11+.

```bash
git clone https://github.com/avnergomes/parana-rural-access-equity.git
cd parana-rural-access-equity
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Download raw data (~40 MB into data/raw/)
python -m src.download_all

# Compute access scores per municipio
python -m src.compute_scores

# Render deliverables
python -m src.render_outputs
```

Then open `output/interactive_map.html` in a browser, or reproduce interactively via `notebooks/01_analysis.ipynb`.

---

## Data sources (all free, all public)

| Source | Dataset | License | Fetched by |
|---|---|---|---|
| IBGE | Malha municipal 2022 (PR subset) | CC0 | `src/data_ibge.py` |
| IBGE | Censo 2022 — populacao rural/urbana por municipio (SIDRA 9923) | CC0 | `src/data_ibge.py` |
| Ministério da Saúde | CNES — atenção básica (PR), via API de dados abertos | Public domain | `src/data_cnes.py` |
| INEP | Censo Escolar 2024 microdata — escolas rurais (PR) | Public domain | `src/data_inep.py` |
| IDR-Paraná | 22 Núcleos Regionais (curated CSV) | Public data | `src/data_ater.py` |

_Exact URLs and version numbers are pinned in `src/config.py`. OSM road-network isochrones are scoped for a v2 (see `docs/future_work.md`); the MVP uses haversine great-circle distance._

---

## Methodology (short)

For each municipality:

1. Estimate rural population from IBGE Censo 2022 (SIDRA 9923).
2. Locate rural-serving facilities: CNES primary-care units, INEP rural schools, IDR-PR extension offices.
3. Compute an Enhanced 2-Step Floating Catchment Area (E2SFCA, Luo & Qi 2009) score per service, with haversine distance, Gaussian decay (β = 30 km), and a 50 km catchment cutoff.
4. Convert each per-service score to a percentile rank and average them into an equal-weight composite.
5. Rank the 364 municipios with meaningful rural population and flag the bottom quintile.

Full methodology, references, and validation choices in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Repository layout

```
parana-rural-access-equity/
├── README.md
├── LICENSE
├── requirements.txt
├── Makefile
├── src/                    # all pipeline modules
│   ├── config.py           # URLs, CRS, constants
│   ├── utils.py            # cached downloads, TLS handling, helpers
│   ├── data_ibge.py        # IBGE malha + SIDRA population
│   ├── data_cnes.py        # CNES primary care (open-data API)
│   ├── data_inep.py        # INEP rural schools (Censo Escolar)
│   ├── data_ater.py        # IDR-PR extension offices
│   ├── access.py           # E2SFCA implementation
│   ├── compute_scores.py   # composite access index
│   ├── render_outputs.py   # matplotlib + folium outputs
│   └── download_all.py     # orchestrator
├── notebooks/
│   └── 01_analysis.ipynb   # narrated end-to-end
├── data/
│   ├── raw/                # untouched downloads (gitignored)
│   └── processed/          # cleaned parquet (gitignored)
├── output/
│   ├── choropleth_access_score.png
│   ├── interactive_map.html
│   ├── bottom_quintile.csv
│   └── figures/            # supporting figures
└── docs/
    ├── METHODOLOGY.md
    ├── WRITEUP_EN.md       # 500-word portfolio narrative
    ├── WRITEUP_PT.md       # versao pt-br
    └── linkedin_posts.md   # PT + EN draft
```

---

## Português (resumo executivo)

**Quais dos 399 municípios do Paraná são menos servidos por saúde, educação rural e extensão rural, considerando sua população rural?**

Análise espacial reprodutível com dados abertos (IBGE, CNES, INEP, IDR-Paraná) e ferramentas abertas (Python + GeoPandas). Todo o pipeline roda em cerca de 20 minutos em uma máquina padrão.

Metodologia completa em [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Narrativa em português: [`docs/WRITEUP_PT.md`](docs/WRITEUP_PT.md).

---

## License

Code: MIT. Data: retains upstream licenses (see table above).

## Author

**Avner Paes Gomes** — Senior Data Scientist, Forest Engineer.
[LinkedIn](https://linkedin.com/in/avnergomes) · [Portfolio](https://avnergomes.github.io/portfolio) · avnerpaesgomes@gmail.com
