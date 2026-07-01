# Methodology

_A concise defence of the modeling choices, with citations._

## Question

> Which of Paraná's 399 municipalities are underserved by rural health, education, and agricultural extension services relative to their rural population?

## Design at a glance

- **Demand:** one point per município, snapped to the geometric centroid of the IBGE 2022 polygon, weighted by `pop_rural` from SIDRA table 9923 (Censo 2022 universe).
- **Supply, three services:**
  - **Health:** primary-care facilities (`codigo_tipo_unidade ∈ {1, 2, 32, 40}`: Posto de Saúde, UBS, and both mobile-unit types) pulled live from the Ministério da Saúde open-data API (`apidadosabertos.saude.gov.br`), filtered to PR with valid coordinates: 3,075 facilities. Capacity = 1 unit per facility.
  - **Education:** schools in the INEP Censo Escolar 2024 with `TP_LOCALIZACAO == 2` (rural) OR `TP_LOCALIZACAO_DIFERENCIADA > 0` (quilombola, assentamento, floresta, ribeirinha, indígena): 1,187 active PR schools. Capacity = `QT_MAT_BAS` (total enrolments), floored at 1 so schools with missing counts still participate. Because the 2024 microdata no longer ships coordinates, each school is anchored to its municipality centroid (see limitation 2).
  - **Extension:** 414 georeferenced IDR-Paraná extension offices from the official IDR unit shapefile (`Unidades_IDR_UTM`), filtered to extension units only: 392 "Unidade Municipal de Extensão" (one per served município) plus 22 "Unidade Regional de Extensão". Research units (Estação/Polo de Pesquisa) and the 2 administrative Sede offices are excluded. Real coordinates, capacity = 1 unit per office. This makes extension the most granular of the three supply layers, with a real, defensible spatial gradient.
- **Distance:** great-circle (haversine) in km, computed from municipal centroids to facility points. Rationale: for a weekend MVP at Paraná scale, network travel-time via OSM would take 1.5–3 hours of compute and multiple hours of dev, without materially changing the ranking. Isochrone routing is listed in `docs/future_work.md` for a v2 pass.
- **Accessibility formula:** Enhanced 2-Step Floating Catchment Area (E2SFCA) as in Luo & Qi (2009):

    ```
    Step 1 (per facility j):
        R_j = C_j / Σ_k [ P_k^rural · W(d_kj) ]     over municipios k within d0 of j

    Step 2 (per municipio i):
        A_i^service = Σ_j [ R_j · W(d_ij) ]         over facilities j within d0 of i
    ```

    where `W(d) = exp(−d²/β²)` (Gaussian decay), `β = 30 km`, and `d0 = 50 km` catchment cutoff.
- **Normalization:** per-service percentile rank in [0, 100]. Rank is outlier-robust, aligns naturally with the "bottom quintile" story, and lets us communicate a score to non-Brazilian reviewers ("bottom 8th percentile for health access") without them needing to interpret raw E2SFCA units.
- **Composite:** equal-weight average of the three per-service percentiles, re-ranked to obtain the composite percentile. Ranked into quintiles (Q1 = worst 20%, Q5 = best 20%). Municipios with fewer than 500 rural residents are flagged `is_ranked = False` and coloured gray in the map so metropolitan capitals don't dominate the quintile boundaries.

## Why these choices

- **E2SFCA over facilities-per-capita**: naïve facilities-per-1000-rural crushes cross-boundary catchment (a UBS 3 km outside the municipal boundary still serves that municipio) and treats municipal borders as impermeable. E2SFCA captures both the supply competition (Step 1) and the reachable supply from each demand point (Step 2). It is the current standard in the peer-reviewed Brazilian health-geography literature (Luo & Wang 2003; Luo & Qi 2009; Delamater 2013).
- **Gaussian decay over step decay**: no ranking artifacts at band edges; matches the Luo & Qi calibration.
- **β = 30 km, d0 = 50 km**: reproduces the Brazilian rural primary-care practical reach used in the literature.
- **Equal weights**: constitutionally defensible (Art. 196 health, Art. 205 education, Law 12.188/2010 PNATER extension) and transparent. Sensitivity to the weighting is reported honestly rather than assumed away (see the Sensitivity section below): bottom-quintile membership is moderately stable (79.5 to 91.8 percent overlap) when weights tilt toward health or extension, which co-vary spatially across Paraná, but rural schooling is the mirror image, so an education-heavy or PC1-derived weighting diverges more. That tension is a finding, and it is why the per-service maps are published alongside the composite.
- **Percentile rank over z-score / min-max**: outlier-robust; directly aligns with quintile-based communication; z-scores assume normality that rural access does not follow.

## Data licenses

| Source | License | Attribution |
|---|---|---|
| IBGE (malhas municipais, SIDRA) | Public domain / CC0 | © IBGE |
| CNES via Ministério da Saúde open-data API | Public domain | © Ministério da Saúde |
| INEP Censo Escolar 2024 | Public domain | © INEP |
| IDR-Paraná official unit shapefile (`Unidades_IDR_UTM`, extension units only) | Public-sector open data | © IDR-Paraná |
| OpenStreetMap (v2 only) | ODbL 1.0 | © OpenStreetMap contributors |

## Limitations

1. **Great-circle distances.** Rugged terrain (Serra do Mar, Serra Geral) makes real travel time non-linear vs. straight-line distance. Planned v2: OSM road-network isochrones via `osmnx.routing` with a per-municipio pre-clipped PBF (see `docs/future_work.md`).
2. **INEP schools anchored to municipal centroids.** The Censo Escolar **2024** microdata no longer publishes school coordinates (INEP dropped LATITUDE/LONGITUDE from the public file). Each rural school is therefore placed at the centroid of its `CO_MUNICIPIO` polygon. This is consistent with the municipal resolution of the analysis, but it removes within-municipality spatial variation for the education service. A v2 could join the INEP "Catálogo de Escolas" (which retains georef) for true school points.
3. **CNES capacity = 1 per unit.** A staffed UBS with 4 equipes de Saúde da Família actually delivers more care than a 1-person Posto. Using `QT_PROF_MED` or `QT_EQUIPES` from CNES `EQ` files would be an easy refinement.
4. **Boundary effects.** Cross-state UBS and schools in São Paulo, Santa Catarina, and Mato Grosso do Sul are ignored. Along the Costa Oeste and Sudoeste the Itaipu reservoir and the Paraguay/Argentina international border cut into the 50 km catchment, so cross-border facilities go uncounted; for these municipios access is understated, which is one reason the worst-off composite cluster sits along that western edge. The E2SFCA d0=50 km catchment somewhat masks the effect for interior municipios.
5. **Centroid ≠ population-weighted centroid.** Using the geometric centroid for demand assumes rural population is uniformly distributed within each municipio, which it is not (population usually clusters near sub-district seats). A v2 pass could compute weighted centroids from IBGE Setores Censitários rural polygons.

## Sensitivity checks

**Weight scheme (executed).** Bottom-quintile (Q1) membership was recomputed under five weightings and compared to the equal-weight baseline (73 municipios):

| Scheme | Q1 overlap vs equal weights |
|---|---|
| Equal (1/3 each) | 100% (baseline) |
| Health-heavy (0.5 / 0.25 / 0.25) | 91.8% |
| Extension-heavy (0.25 / 0.25 / 0.5) | 79.5% |
| Education-heavy (0.25 / 0.5 / 0.25) | 56.2% |
| PC1-derived | 45.2% |

The takeaway is moderate robustness. Q1 is fairly stable when the weighting tilts toward health or extension (91.8% and 79.5% overlap), because primary-care access and extension access co-vary across Paraná (health-vs-extension percentile correlation +0.74): both concentrate in the same more-developed municipios, largely the north and the modernized agricultural belt. Rural-school access is the mirror image (health-vs-education −0.46, education-vs-extension −0.73), strongest in the center-south, so reweighting toward education moves Q1 more (56.2% overlap). The composite's worst-off fifth is therefore where health and extension are both thin at once, and those places tend to have relatively more rural schools. The first principal component loads (health +0.88, education −0.87, extension +0.99), i.e. a (health + extension) *versus* education contrast rather than a shared access axis, which is why its Q1 set overlaps the equal-weight set by only 45.2%. Equal weighting is a transparent normative choice, and the per-service maps are published so a reader can see the education-versus-rest contrast directly.

**Decay parameter and catchment cutoff (scoped for v2).** Recomputing E2SFCA across β ∈ {20, 30, 40} km and d0 ∈ {30, 50, 75} km, and reporting Kendall's τ between the resulting composite rankings, is the natural next robustness pass. It is described here and left for the follow-up rather than claimed.

## References

1. **Luo, W. & Wang, F. (2003).** Measures of spatial accessibility to health care in a GIS environment: synthesis and a case study in the Chicago region. *Environment and Planning B: Planning and Design*, 30(6), 865–884.
2. **Luo, W. & Qi, Y. (2009).** An enhanced two-step floating catchment area (E2SFCA) method for measuring spatial accessibility to primary care physicians. *Health & Place*, 15(4), 1100–1107.
3. **Delamater, P. L. (2013).** Spatial accessibility in suboptimally configured health care systems: A modified two-step floating catchment area (M2SFCA) metric. *Health & Place*, 24, 30–43.
4. **Hansen, W. G. (1959).** How Accessibility Shapes Land Use. *Journal of the American Institute of Planners*, 25(2), 73–76.
5. **Wang, F. (2012).** Measurement, optimization, and impact of health care accessibility: A methodological review. *Annals of the Association of American Geographers*, 102(5), 1104–1112.

Brazilian applied studies (search "acessibilidade espacial atenção primária Brasil 2SFCA" on SciELO for a current example): a family of papers by the Almeida / Andrade / Amaral groups on primary-care spatial accessibility in Minas Gerais, São Paulo, and Pernambuco demonstrates that 2SFCA-family methods are standard practice in Brazilian health geography.
