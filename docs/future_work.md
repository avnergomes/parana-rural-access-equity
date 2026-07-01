# Future work (v2 roadmap)

Explicitly scoped MVP boundaries, called out as "known limitations to fix" rather than gaps that break the piece.

## 1. OSM travel-time isochrones

Replace great-circle distance with drive-time from municipal centroid to each facility via `osmnx.routing`.

**Recipe:**
1. Download Geofabrik `sul-latest.osm.pbf` (~500 MB).
2. `osmium extract -p parana_boundary.geojson sul-latest.osm.pbf -o parana-latest.osm.pbf --strategy=complete_ways`.
3. For each municipio, buffer polygon by 50 km, clip PBF, `pyrosm.OSM(path).get_network(network_type='driving')`, add `travel_time` via `ox.routing.add_edge_speeds` + `ox.routing.add_edge_travel_times`.
4. `nx.ego_graph(G, center_node, radius=1800, distance='travel_time')` → concave hull.
5. Rerun E2SFCA with `d_ij` in seconds and `beta` retuned.

**Cost:** 1.5–3 h compute for 399 municipios single-threaded; ~30–45 min on 6 cores with `multiprocessing`.

**Expected effect on ranking:** tightens health/education scores for Litoral Norte and Vale do Ribeira (steep terrain). Q1 identity likely stable > 90%.

## 2. CNES equipe-level capacity

Currently `capacity = 1` per UBS. Real UBS staffing varies 1–8 equipes de Saúde da Família.

**Recipe:**
- Add CNES `EQ` file join in `data_cnes.py`: `capacity = count(equipes ativas com codigo INE)`.
- Update E2SFCA input.

**Expected effect:** rebalances health score toward regions with denser UBS staffing (Curitiba metro, Cascavel, Londrina). Rural interior likely unchanged since single-equipe UBS dominate there.

## 3. Population-weighted centroids

Currently: geometric centroid of the municipal polygon = demand point. Real rural population clusters near sub-district seats.

**Recipe:**
- Download IBGE Setores Censitários 2022 rural polygons.
- Aggregate `pop_rural` per setor.
- Compute the population-weighted centroid inside each municipality.

**Expected effect:** shifts the demand point for large rural municipios (Pinhão, Tibagi, Ortigueira) by 5–20 km toward the population core. Health/education scores move accordingly.

## 4. INEP real school coordinates (Catálogo de Escolas)

Currently: the 2024 Censo Escolar microdata ships no LATITUDE/LONGITUDE, so every rural school is anchored to its `CO_MUNICIPIO` centroid. This matches the municipal resolution but flattens within-municipality detail.

**Recipe:**
- Join the INEP "Catálogo de Escolas" (which retains georef) on `CO_ENTIDADE` to recover true point coordinates.
- Fall back to the municipal centroid only for schools missing from the catalog, and add a `school_georref_confidence` column (1 = real coords, 0 = centroid fallback).
- Sensitivity analysis: does the education E2SFCA and the Q1 set change materially once schools carry true points instead of centroids?

## 5. Cross-state facilities

Currently: only Paraná facilities count. Border municipios near SP, SC, and MS understate their access.

**Recipe:**
- Extend CNES pull to states SP, SC, MS (via PySUS `state=[...]`).
- Extend INEP filter to same states.
- Keep the E2SFCA d0 catchment (50 km) — cross-state facilities within 50 km of a PR municipio centroid start counting automatically.

**Expected effect:** boosts scores for border municipios in the far south (near SC), far west (near MS), and far north (near SP). ~30 of 399 municipios affected.

## 6. Sensitivity dashboard (Streamlit)

Ship an interactive parameter explorer as a follow-up piece:
- Sliders for β, d0, weights.
- Live update of the quintile classification.
- Downloadable "your parameter choice" CSV.

**Portfolio value:** adds Streamlit / deployment to the skill signal, at the cost of one extra weekend.

## 7. Temporal comparison — Censo 2010 vs 2022

Reuse the same pipeline against SIDRA 4709 (Censo 2010 urbana/rural) and CNES 201008 competencia. Report which municipios improved / regressed in composite access over 12 years.

**Portfolio value:** demonstrates ETL and temporal comparison, closer to what state-level analysts do day-to-day.

## Priority order

1. **INEP coordinate imputation** — cheapest, tightest gain.
2. **OSM travel-time isochrones** — the most obvious question a reviewer asks; makes the piece defensible against senior GIS scrutiny.
3. **Cross-state facilities** — small dev cost, meaningful for ~30 border municipios.
4. **CNES equipe capacity** — medium cost, refines health score.
5. **Population-weighted centroids** — medium cost, refines demand point.
6. **Streamlit sensitivity dashboard** — a separate portfolio piece on its own.
7. **Censo 2010 vs 2022 comparison** — a follow-up study.
