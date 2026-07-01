"""Enhanced 2-Step Floating Catchment Area (E2SFCA) — Luo & Qi (2009).

Given N demand points (municipality centroids with rural population) and
M supply points (facilities with a capacity), this returns an accessibility
score per demand point that reflects both facility scarcity and cross-boundary
catchment overlap.

Distance is great-circle in km (haversine) — good enough for the MVP at the
scale of Parana. A follow-up "v2" can swap in OSRM travel-time.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config
from .utils import log


_EARTH_RADIUS_KM = 6371.0088


def haversine_matrix(
    lats_a: np.ndarray, lons_a: np.ndarray,
    lats_b: np.ndarray, lons_b: np.ndarray,
) -> np.ndarray:
    """Vectorized haversine distance in km between two point sets.

    Shape: (len(a), len(b)).
    """
    la = np.deg2rad(lats_a)[:, None]
    lo = np.deg2rad(lons_a)[:, None]
    lb = np.deg2rad(lats_b)[None, :]
    lob = np.deg2rad(lons_b)[None, :]

    dlat = lb - la
    dlon = lob - lo
    a = np.sin(dlat / 2) ** 2 + np.cos(la) * np.cos(lb) * np.sin(dlon / 2) ** 2
    return 2.0 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def gaussian_decay(distance_km: np.ndarray, beta: float) -> np.ndarray:
    """W(d) = exp(-d^2 / beta^2). Smooth, well-behaved, matches Luo & Qi 2009."""
    return np.exp(-(distance_km ** 2) / (beta ** 2))


@dataclass
class E2SFCAInputs:
    """Everything the E2SFCA formula needs, in numpy form."""

    demand_lat: np.ndarray   # (N,) muni centroid lat
    demand_lon: np.ndarray   # (N,) muni centroid lon
    demand_pop: np.ndarray   # (N,) rural population
    supply_lat: np.ndarray   # (M,) facility lat
    supply_lon: np.ndarray   # (M,) facility lon
    supply_cap: np.ndarray   # (M,) facility capacity (1 for UBS, enrolment for schools)


def compute_e2sfca(
    inp: E2SFCAInputs,
    beta_km: float = config.E2SFCA_BETA_KM,
    d0_km: float = config.E2SFCA_D0_KM,
) -> np.ndarray:
    """Return an (N,) E2SFCA accessibility score per demand point.

    Step 1: for each supply facility j, compute weighted total demand
        R_j = C_j / sum_k (P_k * W(d_kj))    (only over k within d0 of j)
    Step 2: for each demand point i, sum reachable R_j weighted by W
        A_i = sum_j (R_j * W(d_ij))          (only over j within d0 of i)
    """
    n = len(inp.demand_lat)
    m = len(inp.supply_lat)
    if n == 0 or m == 0:
        return np.zeros(n)

    # (N, M) distance matrix
    d = haversine_matrix(
        inp.demand_lat, inp.demand_lon,
        inp.supply_lat, inp.supply_lon,
    )
    # (N, M) decay, masked outside the catchment
    w = gaussian_decay(d, beta_km)
    w[d > d0_km] = 0.0

    # Step 1: supply-to-demand ratio per facility R_j = C_j / sum_k(P_k * W_kj)
    weighted_pop = (inp.demand_pop[:, None] * w).sum(axis=0)  # (M,)
    safe = weighted_pop > 0
    r_j = np.zeros(m)
    r_j[safe] = inp.supply_cap[safe] / weighted_pop[safe]

    # Step 2: accessibility per demand point A_i = sum_j(R_j * W_ij)
    a_i = (r_j[None, :] * w).sum(axis=1)
    return a_i


def score_service(
    demand: gpd.GeoDataFrame,
    supply: gpd.GeoDataFrame,
    *,
    demand_pop_col: str = "pop_rural",
    supply_cap_col: str = "capacity",
    beta_km: float = config.E2SFCA_BETA_KM,
    d0_km: float = config.E2SFCA_D0_KM,
    service_name: str = "service",
) -> pd.Series:
    """One convenience call: E2SFCA on a demand+supply pair. Returns a Series
    indexed by the demand GeoDataFrame's index."""
    # Centroids must be taken in a projected CRS; doing it in EPSG:4674 is both
    # slightly wrong and noisy (geopandas warns). Reproject to UTM 22S, take the
    # centroid, then convert the point back to lon/lat for the haversine matrix.
    demand_cent = demand.geometry.to_crs(config.CRS_METRIC_PR).centroid.to_crs(
        config.CRS_GEOGRAPHIC
    )
    demand_lat = demand_cent.y.to_numpy()
    demand_lon = demand_cent.x.to_numpy()
    supply_lat = supply.geometry.y.to_numpy()
    supply_lon = supply.geometry.x.to_numpy()
    supply_cap = supply[supply_cap_col].astype(float).to_numpy()
    demand_pop = demand[demand_pop_col].fillna(0).astype(float).to_numpy()

    scores = compute_e2sfca(
        E2SFCAInputs(
            demand_lat=demand_lat, demand_lon=demand_lon, demand_pop=demand_pop,
            supply_lat=supply_lat, supply_lon=supply_lon, supply_cap=supply_cap,
        ),
        beta_km=beta_km,
        d0_km=d0_km,
    )
    log().info(
        "%s E2SFCA: %d demand pts, %d supply pts, beta=%.1f km, d0=%.1f km",
        service_name, len(demand_lat), len(supply_lat), beta_km, d0_km,
    )
    return pd.Series(scores, index=demand.index, name=f"{service_name}_e2sfca")
