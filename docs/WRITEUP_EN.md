# Rural service access is not evenly distributed across Paraná

_Which of Paraná's 399 municipalities are underserved by rural health, education, and agricultural extension services relative to their rural population?_

## The question

Rural Paraná is about 1.26 million people, 11 percent of the state's 11.4 million, spread across roughly 200,000 km². Those people rely on three parallel service networks: primary care from Ministério da Saúde (CNES UBS), rural schools from INEP, and agricultural extension from IDR-Paraná. Coverage is universal in theory. In practice, rural residents in some municipios face a long drive to the nearest UBS while others live within walking distance. This project quantifies that gap.

## What I did

I built a reproducible pipeline that:

1. Pulled the 399 Paraná municipal polygons and 2022 Censo rural population (IBGE SIDRA table 9923).
2. Pulled all Paraná primary-care CNES facilities (`codigo_tipo_unidade ∈ {1, 2, 32, 40}`: postos, UBS, mobile units) from the Ministério da Saúde open-data API. That is 3,075 facilities with valid coordinates.
3. Pulled every active rural school from the INEP Censo Escolar 2024 (`TP_LOCALIZACAO == 2` OR `TP_LOCALIZACAO_DIFERENCIADA > 0`): 1,187 schools statewide.
4. Pulled the 22 IDR-Paraná Núcleos Regionais from a curated CSV.
5. Computed an **Enhanced 2-Step Floating Catchment Area** (Luo & Qi, 2009) score per service, with Gaussian distance decay (β = 30 km) and a 50 km catchment cutoff.
6. Converted each per-service score to a percentile rank and averaged them into an equal-weight composite.
7. Ranked the 364 municipios with meaningful rural population into quintiles and flagged the bottom 20% as underserved.

Everything is in Python. Every raw dataset caches to disk. The whole thing runs in about 20 minutes on a laptop.

## What I found

- **Bottom quintile (Q1):** 73 municipios. They cluster in the Centro-Sul and Campos Gerais interior (Tibagi, Candói, Altamira do Paraná, Nova Cantu), the Norte Pioneiro border (Santana and Salto do Itararé), and a cluster of small Costa Oeste municipios wedged against the Itaipu reservoir (Pato Bragado, Santa Helena, Mercedes, Entre Rios do Oeste).
- **Population impact:** 196,356 rural residents, about 1 in 6 of the state's ranked rural population, live in a Q1 municipio.
- **Access gap:** in the worst-served fifth, per-capita raw E2SFCA access runs about 2.2x below the best-served fifth for primary care and about 2.3x below for rural schooling (population-weighted). Extension shows a far larger gap, but that number is dominated by the coarseness of the 22-point ATER layer and should be read as a caveat, not a headline.
- **Robustness:** Q1 membership is moderately stable when the weights tilt toward any single service: 67 to 88 percent of Q1 municipios stay in Q1 under health-heavy, education-heavy, or extension-down schemes. It is *not* stable under a PC1-derived weighting (27 percent overlap), and that is the interesting part. Health and rural schooling are spatially anti-correlated in Paraná (the north is strong on primary care, the center-south on rural schools), so the first principal component captures that tension rather than a shared access axis. I report the per-service maps alongside the composite for exactly this reason.

## Why this framing

I could have counted UBS per 5,000 rural residents and stopped there. That would have been misleading. Naïve facilities-per-capita ignores that a UBS 3 km outside the municipal boundary still serves that municipality's residents, and it treats municipal borders as impermeable. E2SFCA captures both effects, and it is the current standard in the peer-reviewed Brazilian health-geography literature. Full method rationale, citations, and sensitivity checks are in `docs/METHODOLOGY.md`.

Equal weights across the three services reflect a constitutional framing (Art. 196 health; Art. 205 education; Law 12.188/2010 PNATER extension). I report the sensitivity to weight choice as a robustness check rather than pretending one particular weighting is objectively correct.

## Limitations I would want to fix in a v2

- **Great-circle distances** miss terrain drag in the Serra do Mar and Serra Geral. A v2 with OSM road-network isochrones (osmnx pre-clipped PBFs) would tighten the health score for the Litoral Norte and Vale do Ribeira in particular.
- **Boundary effects** pull down the small Costa Oeste municipios on the Itaipu reservoir: their 50 km catchment is cut off by water and the international border, and cross-border Paraguayan facilities do not count. This is real geography, but a national-plus-border catchment would soften it.
- **CNES capacity = 1 unit per facility** underestimates busier UBS with multiple equipes de Saúde da Família. Adding CNES `EQ` file joins would fix this.
- **INEP schools are anchored to the municipal centroid.** The 2024 Censo Escolar microdata no longer publishes school coordinates, so each school is placed at the centroid of its municipality. That matches the municipal resolution of the analysis but loses within-municipality detail; a v2 would join the INEP "Catálogo de Escolas" for true points.
- **The ATER layer is coarse:** 22 regional offices stand in for the whole extension network, which is why the extension access gap is large and volatile. Municipal-level ATER unit locations would refine it.
- **Cross-state facilities** are ignored. Border municipios near SP, SC, and MS would score slightly better with a national-scale catchment.

## What this piece is meant to show

The map is the surface. What sits under it is a reproducible geospatial pipeline that ingests three federal datasets, applies a peer-reviewed accessibility formula, normalizes into a shareable summary, and produces both a static portfolio-grade choropleth and an interactive Folium map. Every parameter is in `src/config.py`. Every source is versioned. The `Makefile` reproduces the whole thing from scratch in one line.

The `parana-rural-access-equity` repo is one weekend of work. The pattern (public data to E2SFCA to percentile rank to quintile choropleth to bilingual writeup) generalizes to any US or European region. Swap out IBGE for TIGER/Line + ACS, CNES for state health facility registers, INEP for state education directories. The pipeline is the portfolio piece.

**Repo:** `github.com/avnergomes/parana-rural-access-equity`
**Live map:** `avnergomes.github.io/parana-rural-access-equity/`
**Methodology + refs:** [`docs/METHODOLOGY.md`](METHODOLOGY.md)
**Contact:** Avner Paes Gomes · avnerpaesgomes@gmail.com · [LinkedIn](https://linkedin.com/in/avnergomes)
