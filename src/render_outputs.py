"""Render the portfolio deliverables from `pr_muni_access_scores.gpkg`.

Produces:
    output/choropleth_access_score.png     — static, 200 dpi, for CVs and slides
    output/interactive_map.html            — folium, tooltip, bottom-quintile overlay
    output/bottom_quintile.csv             — the underserved municipios
    output/figures/access_by_service.png   — 3 mini choropleths for the writeup
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap

from . import config
from .utils import log


# Sequential palette. Q1 = worst access = dark red; Q5 = best = pale.
QUINTILE_COLORS = ["#7f0000", "#d7301f", "#fc8d59", "#fdcc8a", "#fef0d9"]
QUINTILE_LABELS = [
    "Q1 – worst 20%",
    "Q2",
    "Q3",
    "Q4",
    "Q5 – best 20%",
]


def _load_scored() -> gpd.GeoDataFrame:
    path = config.DATA_PROCESSED / "pr_muni_access_scores.gpkg"
    if not path.exists():
        raise FileNotFoundError(
            f"missing {path}. Run `python -m src.compute_scores` first."
        )
    gdf = gpd.read_file(path)
    # GeoPackage can round-trip `quintile` back as a string; coerce so every
    # `quintile == 1` comparison downstream behaves numerically.
    if "quintile" in gdf.columns:
        gdf["quintile"] = pd.to_numeric(gdf["quintile"], errors="coerce")
    return gdf


# ---------------------------------------------------------------------------
# 1. Static PNG choropleth
# ---------------------------------------------------------------------------

def render_static(gdf: gpd.GeoDataFrame) -> None:
    """The map that goes into the CV and in the LinkedIn card."""
    fig, ax = plt.subplots(figsize=(11, 9), dpi=200)

    # Unranked (near-zero rural population) get a neutral gray so they don't
    # visually pollute the quintile story.
    unranked = gdf[~gdf["is_ranked"]]
    ranked = gdf[gdf["is_ranked"]]

    if not unranked.empty:
        unranked.plot(
            ax=ax,
            color="#e8e8e8",
            edgecolor="white",
            linewidth=0.2,
        )

    cmap = ListedColormap(QUINTILE_COLORS)
    ranked.plot(
        column="quintile",
        cmap=cmap,
        edgecolor="white",
        linewidth=0.2,
        ax=ax,
        categorical=True,
        legend=True,
        legend_kwds={
            "title": "Access quintile\n(rural composite, E2SFCA)",
            "labels": QUINTILE_LABELS,
            "loc": "lower left",
            "frameon": False,
        },
    )

    ax.set_axis_off()
    ax.set_title(
        "Rural service access in Paraná, Brazil\n"
        "Composite E2SFCA: primary care (CNES), rural schools (INEP), "
        "extension offices (IDR-PR)\n"
        f"n = {len(ranked)} municipalities ranked · Censo 2022 · "
        "β=30 km Gaussian decay, d₀=50 km catchment",
        loc="left",
        fontsize=10.5,
        pad=12,
    )
    ax.annotate(
        "Data: IBGE Censo 2022, DATASUS/CNES, INEP Censo Escolar, IDR-Paraná. "
        "Method: Enhanced 2SFCA (Luo & Qi 2009), equal-weight composite of "
        "per-service percentile ranks.",
        xy=(0, -0.02),
        xycoords="axes fraction",
        fontsize=7.5,
        color="#555",
    )

    dest = config.OUTPUT_DIR / "choropleth_access_score.png"
    fig.savefig(dest, bbox_inches="tight", dpi=200)
    plt.close(fig)
    log().info("wrote %s", dest.name)


# ---------------------------------------------------------------------------
# 2. Per-service mini-choropleths (writeup supporting figure)
# ---------------------------------------------------------------------------

def render_per_service_grid(gdf: gpd.GeoDataFrame) -> None:
    services = ("health", "education", "extension")
    titles = ("Health (CNES UBS)", "Education (INEP rural)", "Extension (IDR-PR)")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), dpi=180)
    for ax, service, title in zip(axes, services, titles):
        col = f"{service}_pct"
        gdf.plot(
            column=col,
            cmap="YlOrRd_r",
            ax=ax,
            edgecolor="white",
            linewidth=0.15,
            legend=True,
            legend_kwds={"shrink": 0.55, "label": "percentile (0=worst)"},
            missing_kwds={"color": "#e8e8e8"},
        )
        ax.set_axis_off()
        ax.set_title(title, fontsize=11)

    fig.suptitle(
        "Per-service access percentiles across Paraná municípios",
        fontsize=13, y=1.02,
    )
    fig.tight_layout()
    dest = config.FIGURES_DIR / "access_by_service.png"
    fig.savefig(dest, bbox_inches="tight", dpi=180)
    plt.close(fig)
    log().info("wrote %s", dest.relative_to(config.OUTPUT_DIR))


# ---------------------------------------------------------------------------
# 3. Interactive Folium map
# ---------------------------------------------------------------------------

def render_interactive(gdf: gpd.GeoDataFrame) -> None:
    """The map users click on the portfolio site."""
    import folium
    import branca.colormap as cm

    gdf_web = gdf.to_crs(config.CRS_GEOGRAPHIC).copy()
    # Simplify geoms so the HTML stays small.
    gdf_web["geometry"] = gdf_web.geometry.simplify(0.001, preserve_topology=True)

    # Round percentile + quintile columns for a clean tooltip. localize=True
    # would otherwise render 33.836 as "33,836" (looks like 33k); integers read
    # cleanly while population still gets its thousands separator.
    for c in ("composite_pct", "health_pct", "education_pct", "extension_pct"):
        if c in gdf_web.columns:
            gdf_web[c] = gdf_web[c].round(0).astype("Int64")
    if "quintile" in gdf_web.columns:
        gdf_web["quintile"] = pd.to_numeric(
            gdf_web["quintile"], errors="coerce"
        ).astype("Int64")

    ranked = gdf_web[gdf_web["is_ranked"]]

    m = folium.Map(
        location=[-24.5, -51.5],
        zoom_start=7,
        tiles="cartodbpositron",
        control_scale=True,
    )

    colormap = cm.LinearColormap(
        colors=QUINTILE_COLORS,
        vmin=0, vmax=100,
        caption="Composite access percentile (0 = worst, 100 = best)",
    )

    def _style(feat):
        v = feat["properties"].get("composite_pct")
        if v is None:
            return {"fillColor": "#e8e8e8", "color": "white", "weight": 0.3, "fillOpacity": 0.4}
        return {
            "fillColor": colormap(v),
            "color": "white",
            "weight": 0.3,
            "fillOpacity": 0.85,
        }

    tooltip_fields = [
        "NM_MUN", "pop_rural", "composite_pct",
        "health_pct", "education_pct", "extension_pct", "quintile",
    ]
    tooltip_aliases = [
        "Município", "Rural pop.", "Composite pctile",
        "Health pctile", "Education pctile", "Extension pctile", "Quintile",
    ]

    folium.GeoJson(
        ranked,
        style_function=_style,
        highlight_function=lambda f: {"weight": 2, "color": "#222"},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=False,
        ),
        name="Ranked municípios",
    ).add_to(m)

    # Bottom-quintile emphasis overlay.
    bottom = ranked[ranked["quintile"] == 1]
    if not bottom.empty:
        folium.GeoJson(
            bottom,
            style_function=lambda f: {
                "fillOpacity": 0,
                "color": "#111",
                "weight": 1.4,
                "dashArray": "4,3",
            },
            name=f"Bottom quintile ({len(bottom)} municípios)",
        ).add_to(m)

    colormap.add_to(m)
    folium.LayerControl().add_to(m)

    dest = config.OUTPUT_DIR / "interactive_map.html"
    m.save(str(dest))
    log().info("wrote %s (%.1f KB)", dest.name, dest.stat().st_size / 1024)


# ---------------------------------------------------------------------------
# 4. Underserved-municipios CSV
# ---------------------------------------------------------------------------

def render_underserved_csv(gdf: gpd.GeoDataFrame) -> None:
    """The audit trail: exactly which municipios are in the bottom quintile."""
    cols = [
        "CD_MUN", "NM_MUN",
        "pop_total", "pop_urbana", "pop_rural",
        "health_e2sfca", "education_e2sfca", "extension_e2sfca",
        "health_pct", "education_pct", "extension_pct",
        "composite_pct", "quintile", "underserved",
    ]
    df = pd.DataFrame(gdf[cols])
    dest_full = config.OUTPUT_DIR / "muni_access_scores.csv"
    df.to_csv(dest_full, index=False, encoding="utf-8")
    log().info("wrote %s (%d rows)", dest_full.name, len(df))

    bottom = df[df["quintile"] == 1].sort_values("composite_pct")
    dest_bottom = config.OUTPUT_DIR / "bottom_quintile.csv"
    bottom.to_csv(dest_bottom, index=False, encoding="utf-8")
    log().info("wrote %s (%d rows)", dest_bottom.name, len(bottom))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-interactive", action="store_true", help="skip Folium HTML")
    args = ap.parse_args()

    gdf = _load_scored()
    render_static(gdf)
    render_per_service_grid(gdf)
    render_underserved_csv(gdf)
    if not args.skip_interactive:
        render_interactive(gdf)


if __name__ == "__main__":
    main()
