"""Interactive, narrative-driven report for the Parana Rural Access Equity study.

Builds a self-contained, magazine-quality HTML report (one file per language)
in the portfolio "Midnight" aesthetic, with embedded Plotly charts and a
storytelling arc: the coverage question, the composite map, the three-service
surprise, where the gaps stack up, how robust it is, and how it was built.

Trilingual scaffolding, ships PT + EN. Run `python -m src.report`.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo

from . import config
from .utils import log

# --------------------------------------------------------------------------- palette
PAPER = "#0d1320"
INK = "#e7ecf3"
INK2 = "#c2ccd9"
MUT = "#8b97a8"
AMBER = "#e3a857"
BLUE = "#6ea8fe"
GREEN = "#56d49b"
RED = "#f08a7f"
VIOLET = "#b89cff"
GRID = "rgba(255,255,255,0.09)"

# Access colorscale: low percentile (worst access) = deep red, high = teal-green.
ACCESS_SCALE = [
    [0.00, "#7f0000"], [0.20, "#c1341d"], [0.40, "#e3773f"],
    [0.60, "#e7b56a"], [0.80, "#7cae8f"], [1.00, "#2f8f6b"],
]
QUINTILE_COLORS = {1: "#7f0000", 2: "#d7301f", 3: "#fc8d59", 4: "#7cae8f", 5: "#2f8f6b"}

LANGS = ("pt", "en")
LANG_NAME = {"pt": "Portugues", "en": "English"}
FILENAME = {"pt": "parana_access_report_pt.html", "en": "parana_access_report_en.html"}


# --------------------------------------------------------------------------- formatting
def br(v, dec=0, lang="pt"):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    s = f"{v:,.{dec}f}"
    if lang == "en":
        return s
    return s.replace(",", "·").replace(".", ",").replace("·", ".")


def pct(v, dec=0, lang="pt"):
    s = f"{v:.{dec}f}"
    if lang != "en":
        s = s.replace(".", ",")
    return s + "%"


def xmult(v, dec=1, lang="pt"):
    s = f"{v:.{dec}f}"
    if lang != "en":
        s = s.replace(".", ",")
    return s + "×"


# --------------------------------------------------------------------------- data
def load_scored() -> gpd.GeoDataFrame:
    g = gpd.read_file(config.DATA_PROCESSED / "pr_muni_access_scores.gpkg")
    g["quintile"] = pd.to_numeric(g["quintile"], errors="coerce")
    return g


def layer_counts() -> dict:
    counts = {}
    for key, fname in (
        ("health", "cnes_pr_primary_202605.gpkg"),
        ("education", "inep_pr_rural_2024.gpkg"),
        ("extension", "ater_pr_stations.gpkg"),
    ):
        p = config.DATA_PROCESSED / fname
        counts[key] = int(len(gpd.read_file(p))) if p.exists() else 0
    return counts


def narrative_stats(g: gpd.GeoDataFrame) -> dict:
    ranked = g[g["is_ranked"]].copy()
    bottom = ranked[ranked["quintile"] == 1]
    top = ranked[ranked["quintile"] == config.NUM_QUINTILES]

    def wmean(df, col):
        w = df["pop_rural"].fillna(0).to_numpy(float)
        v = df[col].fillna(0).to_numpy(float)
        return float((v * w).sum() / max(w.sum(), 1.0))

    gaps = {}
    for svc in ("health", "education", "extension"):
        mb = wmean(bottom, f"{svc}_e2sfca")
        mt = wmean(top, f"{svc}_e2sfca")
        gaps[svc] = mt / mb if mb > 0 else float("nan")

    h, e, x = ranked["health_pct"], ranked["education_pct"], ranked["extension_pct"]
    corr = {
        "he": float(h.corr(e)),
        "hx": float(h.corr(x)),
        "ex": float(e.corr(x)),
    }

    # weight-scheme sensitivity (Q1 membership overlap vs equal weights)
    def bottom_set(series):
        cut = series.quantile(0.20)
        return set(series[series <= cut].index)

    schemes = {
        "equal": (h + e + x) / 3,
        "health": 0.5 * h + 0.25 * e + 0.25 * x,
        "extension": 0.25 * h + 0.25 * e + 0.5 * x,
        "education": 0.25 * h + 0.5 * e + 0.25 * x,
    }
    svc = ranked[["health_pct", "education_pct", "extension_pct"]].dropna()
    z = (svc - svc.mean()) / svc.std()
    _, evec = np.linalg.eigh(np.cov(z.values.T))
    w = evec[:, -1]
    if w.sum() < 0:
        w = -w
    w = w / w.sum()
    schemes["pc1"] = pd.Series(svc.values @ w, index=svc.index).reindex(ranked.index)
    base = bottom_set(schemes["equal"].dropna())
    overlap = {
        k: 100 * len(bottom_set(s.dropna()) & base) / max(len(base), 1)
        for k, s in schemes.items()
    }

    worst = ranked.nsmallest(15, "composite_pct")

    return dict(
        rural_total=float(g["pop_rural"].sum()),
        pop_total=float(g["pop_total"].sum()),
        rural_pct=100 * g["pop_rural"].sum() / g["pop_total"].sum(),
        n_ranked=int(ranked.shape[0]),
        n_total=int(g.shape[0]),
        bottom_n=int(bottom.shape[0]),
        bottom_pop=float(bottom["pop_rural"].sum()),
        ranked_pop=float(ranked["pop_rural"].sum()),
        bottom_share=100 * bottom["pop_rural"].sum() / ranked["pop_rural"].sum(),
        gaps=gaps,
        corr=corr,
        overlap=overlap,
        pc1_w=[float(v) for v in w],
        worst=worst,
        ranked=ranked,
    )


# --------------------------------------------------------------------------- geojson
def build_geojson(g: gpd.GeoDataFrame) -> dict:
    gj = g.copy()
    gj["geometry"] = gj.geometry.simplify(0.008, preserve_topology=True)
    gj = gj.to_crs(config.CRS_GEOGRAPHIC)
    feats = []
    for _, row in gj.iterrows():
        feats.append({
            "type": "Feature",
            "id": row["CD_MUN"],
            "geometry": row["geometry"].__geo_interface__,
            "properties": {"NM_MUN": row["NM_MUN"]},
        })
    return {"type": "FeatureCollection", "features": feats}


# --------------------------------------------------------------------------- plotly
def div(fig) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": False, "responsive": True})


def fig_switcher_map(g, gj, S):
    """One choropleth with buttons to switch surface: composite + 3 services."""
    ranked = g[g["is_ranked"]]
    surfaces = [
        ("composite_pct", S["m_composite"]),
        ("health_pct", S["m_health"]),
        ("education_pct", S["m_education"]),
        ("extension_pct", S["m_extension"]),
    ]
    fig = go.Figure()
    for i, (col, name) in enumerate(surfaces):
        fig.add_trace(go.Choroplethmap(
            geojson=gj, locations=ranked["CD_MUN"], z=ranked[col],
            featureidkey="id", colorscale=ACCESS_SCALE, zmin=0, zmax=100,
            marker=dict(line=dict(width=0.3, color="rgba(255,255,255,0.18)")),
            colorbar=dict(title=dict(text=S["m_cbar"], font=dict(color=INK2, size=11)),
                          tickfont=dict(color=INK2, size=11), thickness=12, len=0.72,
                          x=0.99, xanchor="right", bgcolor="rgba(0,0,0,0)"),
            customdata=ranked[["NM_MUN"]],
            hovertemplate="<b>%{customdata[0]}</b><br>" + S["m_pctile"] + ": %{z:.0f}<extra></extra>",
            visible=(i == 0), name=name,
        ))
    buttons = []
    for i, (_, name) in enumerate(surfaces):
        vis = [j == i for j in range(len(surfaces))]
        buttons.append(dict(label=name, method="update", args=[{"visible": vis}]))
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        map=dict(style="carto-darkmatter", center=dict(lat=-24.6, lon=-51.6), zoom=5.55),
        font=dict(color=INK2),
        updatemenus=[dict(
            type="buttons", direction="right", x=0.01, xanchor="left", y=0.99, yanchor="top",
            pad=dict(l=6, r=6, t=6, b=6), bgcolor="rgba(20,26,40,0.85)",
            bordercolor=GRID, borderwidth=1, active=0,
            font=dict(color=INK2, size=12, family="JetBrains Mono, monospace"),
            buttons=buttons,
        )],
    )
    return fig


def fig_covariation(st, S):
    r = st["ranked"]
    fig = go.Figure()
    # health vs extension (positive)
    fig.add_trace(go.Scatter(
        x=r["health_pct"], y=r["extension_pct"], mode="markers",
        marker=dict(size=6, color=GREEN, opacity=0.55, line=dict(width=0)),
        customdata=r[["NM_MUN"]],
        hovertemplate="<b>%{customdata[0]}</b><br>" + S["cv_h"] + ": %{x:.0f}<br>" + S["cv_x"] + ": %{y:.0f}<extra></extra>",
        name=S["cv_hx"].format(r=xcorr(st["corr"]["hx"], S["lang"])),
    ))
    # health vs education (negative)
    fig.add_trace(go.Scatter(
        x=r["health_pct"], y=r["education_pct"], mode="markers",
        marker=dict(size=6, color=RED, opacity=0.55, line=dict(width=0)),
        customdata=r[["NM_MUN"]],
        hovertemplate="<b>%{customdata[0]}</b><br>" + S["cv_h"] + ": %{x:.0f}<br>" + S["cv_e"] + ": %{y:.0f}<extra></extra>",
        name=S["cv_he"].format(r=xcorr(st["corr"]["he"], S["lang"])),
    ))
    # trend lines
    for col, color in (("extension_pct", GREEN), ("education_pct", RED)):
        m, b = np.polyfit(r["health_pct"], r[col], 1)
        xs = np.array([0, 100])
        fig.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines",
                                 line=dict(color=color, width=2, dash="solid"),
                                 hoverinfo="skip", showlegend=False, opacity=0.9))
    fig.update_layout(
        template="plotly_dark", height=480, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=60, r=24, t=10, b=50),
        legend=dict(orientation="h", y=1.06, x=0, font=dict(size=12.5, color=INK2), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title=S["cv_xaxis"], range=[-2, 102], showgrid=True, gridcolor=GRID, color=INK2, zeroline=False),
        yaxis=dict(title=S["cv_yaxis"], range=[-2, 102], showgrid=True, gridcolor=GRID, color=INK2, zeroline=False),
        separators="." if S["lang"] == "en" else ",.",
    )
    return fig


def xcorr(v, lang="pt"):
    s = f"{v:+.2f}"
    return s if lang == "en" else s.replace(".", ",")


def fig_gaps(st, S):
    svc = [("health", S["svc_health"], BLUE), ("extension", S["svc_extension"], GREEN),
           ("education", S["svc_education"], AMBER)]
    svc = sorted(svc, key=lambda s: st["gaps"][s[0]], reverse=True)
    fig = go.Figure(go.Bar(
        y=[s[1] for s in svc], x=[st["gaps"][s[0]] for s in svc], orientation="h",
        marker=dict(color=[s[2] for s in svc]),
        text=[xmult(st["gaps"][s[0]], 1, S["lang"]) for s in svc],
        textposition="outside", textfont=dict(color=INK, size=15),
        hovertemplate="%{y}: %{x:.1f}x<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", height=300, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=140, r=50, t=10, b=40),
        xaxis=dict(title=S["gap_xaxis"], showgrid=True, gridcolor=GRID, color=INK2, zeroline=False, range=[0, max(st["gaps"].values()) * 1.18]),
        yaxis=dict(color=INK, tickfont=dict(size=14)),
        separators="." if S["lang"] == "en" else ",.",
    )
    fig.add_vline(x=1, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"))
    return fig


def fig_sensitivity(st, S):
    order = ["equal", "health", "extension", "education", "pc1"]
    labels = [S["sc_equal"], S["sc_health"], S["sc_extension"], S["sc_education"], S["sc_pc1"]]
    vals = [st["overlap"][k] for k in order]
    colors = [MUT, BLUE, GREEN, AMBER, VIOLET]
    fig = go.Figure(go.Bar(
        x=labels, y=vals, marker=dict(color=colors),
        text=[pct(v, 1, S["lang"]) for v in vals], textposition="outside",
        textfont=dict(color=INK, size=13),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", height=340, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=50, r=20, t=16, b=70),
        xaxis=dict(color=INK2, tickfont=dict(size=12)),
        yaxis=dict(title=S["sc_yaxis"], range=[0, 108], showgrid=True, gridcolor=GRID, color=INK2),
        separators="." if S["lang"] == "en" else ",.",
    )
    return fig


def fig_worst(st, S):
    w = st["worst"].sort_values("composite_pct", ascending=False)
    colors = [QUINTILE_COLORS.get(int(q) if pd.notna(q) else 1, RED) for q in w["quintile"]]
    fig = go.Figure(go.Bar(
        y=w["NM_MUN"], x=w["composite_pct"], orientation="h",
        marker=dict(color=colors),
        customdata=w[["pop_rural"]],
        hovertemplate="<b>%{y}</b><br>" + S["w_pctile"] + ": %{x:.1f}<br>" + S["w_pop"] + ": %{customdata[0]:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", height=460, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=160, r=30, t=10, b=40),
        xaxis=dict(title=S["w_xaxis"], showgrid=True, gridcolor=GRID, color=INK2, zeroline=False),
        yaxis=dict(color=INK, tickfont=dict(size=12.5)),
        separators="." if S["lang"] == "en" else ",.",
    )
    return fig


# --------------------------------------------------------------------------- html pieces
def stat(value, label, note="", tone="ink"):
    return (f'<div class="stat tone-{tone}"><div class="stat-v">{value}</div>'
            f'<div class="stat-l">{label}</div><div class="stat-n">{note}</div></div>')


def muni_table(st, S):
    rows = ""
    df = st["ranked"].sort_values("composite_pct")
    for _, r in df.iterrows():
        q = int(r["quintile"]) if pd.notna(r["quintile"]) else 0
        rows += (f'<tr><td>{r["NM_MUN"]}</td>'
                 f'<td class="num">{br(r["pop_rural"], 0, S["lang"])}</td>'
                 f'<td class="num">{r["health_pct"]:.0f}</td>'
                 f'<td class="num">{r["education_pct"]:.0f}</td>'
                 f'<td class="num">{r["extension_pct"]:.0f}</td>'
                 f'<td class="num mono">{r["composite_pct"]:.0f}</td>'
                 f'<td class="num">Q{q}</td></tr>')
    return (f'<table class="tbl sortable"><thead><tr>'
            f'<th>{S["th_muni"]}</th><th>{S["th_pop"]}</th><th>{S["th_health"]}</th>'
            f'<th>{S["th_education"]}</th><th>{S["th_extension"]}</th>'
            f'<th>{S["th_composite"]}</th><th>{S["th_quintile"]}</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>')


# --------------------------------------------------------------------------- imports of CSS + strings
from .report_assets import CSS, PROG_JS, STR_ALL  # noqa: E402


def lang_switch(cur):
    links = ""
    for lg in LANGS:
        on = " on" if lg == cur else ""
        links += f'<a class="{on.strip()}" href="{FILENAME[lg]}">{lg.upper()}</a>'
    return f'<span class="langs">{links}</span>'


def build(lang, g, gj, st, counts):
    S = dict(STR_ALL[lang])
    S["lang"] = lang

    d_map = div(fig_switcher_map(g, gj, S))
    d_cov = div(fig_covariation(st, S))
    d_gap = div(fig_gaps(st, S))
    d_sens = div(fig_sensitivity(st, S))
    d_worst = div(fig_worst(st, S))
    table = muni_table(st, S)
    plotlyjs = pyo.get_plotlyjs()

    total_points = counts["health"] + counts["education"] + counts["extension"]

    ctx = dict(
        rural_total=br(st["rural_total"], 0, lang),
        rural_pct=pct(st["rural_pct"], 0, lang),
        pop_total=br(st["pop_total"], 0, lang),
        n_ranked=br(st["n_ranked"], 0, lang),
        n_total=st["n_total"],
        bottom_n=st["bottom_n"],
        bottom_pop=br(st["bottom_pop"], 0, lang),
        bottom_share=pct(st["bottom_share"], 0, lang),
        cnes=br(counts["health"], 0, lang),
        inep=br(counts["education"], 0, lang),
        ater=br(counts["extension"], 0, lang),
        points=br(total_points, 0, lang),
        gap_h=xmult(st["gaps"]["health"], 1, lang),
        gap_x=xmult(st["gaps"]["extension"], 1, lang),
        gap_e=xmult(st["gaps"]["education"], 1, lang),
        corr_hx=xcorr(st["corr"]["hx"], lang),
        corr_he=xcorr(st["corr"]["he"], lang),
        corr_ex=xcorr(st["corr"]["ex"], lang),
        ov_health=pct(st["overlap"]["health"], 1, lang),
        ov_education=pct(st["overlap"]["education"], 1, lang),
        ov_pc1=pct(st["overlap"]["pc1"], 1, lang),
        worst1=st["worst"].iloc[0]["NM_MUN"],
    )

    def T(key):
        return S[key].format(**ctx)

    refs = (
        '<ol class="refs">'
        '<li><b>Luo, W. &amp; Qi, Y.</b> (2009). An enhanced two-step floating catchment area '
        '(E2SFCA) method for measuring spatial accessibility to primary care physicians. '
        '<i>Health &amp; Place</i>, 15(4), 1100-1107. '
        '<a href="https://doi.org/10.1016/j.healthplace.2009.06.002" target="_blank" rel="noopener">doi:10.1016/j.healthplace.2009.06.002</a></li>'
        '<li><b>Luo, W. &amp; Wang, F.</b> (2003). Measures of spatial accessibility to health care in a GIS environment. '
        '<i>Environment and Planning B</i>, 30(6), 865-884. '
        '<a href="https://doi.org/10.1068/b29120" target="_blank" rel="noopener">doi:10.1068/b29120</a></li>'
        '<li><b>Wang, F.</b> (2012). Measurement, optimization, and impact of health care accessibility. '
        '<i>Annals of the AAG</i>, 102(5), 1104-1112. '
        '<a href="https://doi.org/10.1080/00045608.2012.657146" target="_blank" rel="noopener">doi:10.1080/00045608.2012.657146</a></li>'
        '</ol>'
    )

    site = "https://avnergomes.github.io/parana-rural-access-equity"
    dev = (f'<a class="dev-link" href="https://avnergomes.github.io/portfolio/" target="_blank" rel="noopener">'
           f'{S["ft_by"]} <strong>Avner Gomes</strong></a>')

    html = f"""<!doctype html><html lang="{S['html_lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{S['title']}</title>
<meta name="description" content="{S['meta_desc']}">
<meta name="theme-color" content="#0d1320">
<meta property="og:type" content="article">
<meta property="og:title" content="{S['title']}">
<meta property="og:description" content="{S['meta_desc']}">
<meta property="og:url" content="{site}/output/{FILENAME[lang]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style><script>{plotlyjs}</script></head><body>
<div id="prog"></div>
<nav class="top"><div class="wrap">
  <span class="brand">{S['brand']}</span>
  <a href="#coverage">{S['nav_coverage']}</a><a href="#map">{S['nav_map']}</a>
  <a href="#services">{S['nav_services']}</a><a href="#gaps">{S['nav_gaps']}</a>
  <a href="#robust">{S['nav_robust']}</a><a href="#method">{S['nav_method']}</a>
  <a href="#table">{S['nav_table']}</a>
  {lang_switch(lang)}
</div></nav>

<header class="hero"><div class="wrap">
  <div class="kicker">{S['hero_kicker']}</div>
  <h1>{S['hero_title']}</h1>
  <p class="thesis">{S['hero_thesis']}</p>
  <div class="hero-strip">
    <div class="hs"><div class="v">{ctx['bottom_n']}</div><div class="l">{S['hs1']}</div></div>
    <div class="hs"><div class="v">{S['hs2_v']}</div><div class="l">{T('hs2')}</div></div>
    <div class="hs"><div class="v">{ctx['points']}</div><div class="l">{S['hs3']}</div></div>
    <div class="hs"><div class="v">{ctx['gap_h']}</div><div class="l">{S['hs4']}</div></div>
  </div>
  <div class="src">{T('src')}</div>
</div></header>

<section id="coverage"><div class="wrap">
  <div class="kicker">{S['co_kicker']}</div>
  <h2>{S['co_h2']}</h2>
  <p class="lede">{T('co_lede')}</p>
  <div class="prose"><p>{T('co_p1')}</p><p>{T('co_p2')}</p></div>
  <div class="findings">
    {stat(ctx['rural_total'], S['co_f1'], T('co_f1n'), 'ink')}
    {stat(ctx['cnes'], S['co_f2'], S['co_f2n'], 'blue')}
    {stat(ctx['inep'], S['co_f3'], S['co_f3n'], 'amber')}
    {stat(ctx['ater'], S['co_f4'], S['co_f4n'], 'green')}
  </div>
</div></section>

<section id="map" class="alt"><div class="wrap">
  <div class="kicker">{S['mp_kicker']}</div>
  <h2>{S['mp_h2']}</h2>
  <p class="lede">{T('mp_lede')}</p>
  <div class="fig">{d_map}<div class="figcap">{S['mp_cap']}</div></div>
  <div class="prose"><p>{T('mp_p1')}</p></div>
  <div class="pull">{S['mp_pull']}</div>
</div></section>

<section id="services"><div class="wrap">
  <div class="kicker">{S['sv_kicker']}</div>
  <h2>{S['sv_h2']}</h2>
  <p class="lede">{T('sv_lede')}</p>
  <div class="fig">{d_cov}<div class="figcap">{T('sv_cap')}</div></div>
  <div class="prose"><p>{T('sv_p1')}</p><p>{T('sv_p2')}</p></div>
  <div class="callout">{T('sv_callout')}</div>
</div></section>

<section id="gaps" class="alt"><div class="wrap">
  <div class="kicker">{S['gp_kicker']}</div>
  <h2>{S['gp_h2']}</h2>
  <p class="lede">{T('gp_lede')}</p>
  <div class="grid2">
    <div class="fig">{d_gap}<div class="figcap">{S['gp_cap']}</div></div>
    <div class="prose"><p>{T('gp_p1')}</p></div>
  </div>
  <p class="lede" style="margin-top:38px">{T('gp_lede2')}</p>
  <div class="fig">{d_worst}<div class="figcap">{S['gp_cap2']}</div></div>
</div></section>

<section id="robust"><div class="wrap">
  <div class="kicker">{S['rb_kicker']}</div>
  <h2>{S['rb_h2']}</h2>
  <p class="lede">{T('rb_lede')}</p>
  <div class="grid2">
    <div class="fig">{d_sens}<div class="figcap">{S['rb_cap']}</div></div>
    <div class="prose"><p>{T('rb_p1')}</p></div>
  </div>
</div></section>

<section id="method" class="alt"><div class="wrap">
  <div class="kicker">{S['mt_kicker']}</div>
  <h2>{S['mt_h2']}</h2>
  <p class="lede">{S['mt_lede']}</p>
  <div class="prose"><p>{T('mt_p1')}</p><p>{S['mt_p2']}</p></div>
  <h2 style="font-size:clamp(20px,2.6vw,26px);margin:36px 0 4px">{S['mt_refs_h']}</h2>
  {refs}
  <p class="disc">{S['mt_disc']}</p>
</div></section>

<section id="table"><div class="wrap">
  <div class="kicker">{S['tb_kicker']}</div>
  <h2>{S['tb_h2']}</h2>
  <p class="lede">{S['tb_lede']}</p>
  {table}
</div></section>

<footer><div class="wrap">{T('ft_body')}<br>{dev}</div></footer>
<script>{PROG_JS}</script>
</body></html>"""

    out = config.OUTPUT_DIR / FILENAME[lang]
    out.write_text(html, encoding="utf-8")
    log().info("wrote %s (%.1f MB)", out.name, out.stat().st_size / 1e6)
    return out


def build_all():
    g = load_scored()
    counts = layer_counts()
    st = narrative_stats(g)
    gj = build_geojson(g)
    outs = [build(lang, g, gj, st, counts) for lang in LANGS]
    return outs


if __name__ == "__main__":
    build_all()
