"""Static assets for src/report.py: the Midnight design system (CSS), the
progress/sortable-table script, and the bilingual narrative strings.

Kept separate so the report generator stays about data and figures, and the
long prose lives in one place. Voice: no em-dashes (Avner is the author).
"""

CSS = r"""
:root{
--paper:oklch(14% 0.025 250);--paper-2:oklch(18% 0.03 250);--paper-3:oklch(22% 0.035 250);
--ink:oklch(96% 0.01 250);--ink-2:oklch(82% 0.015 250);--mut:oklch(60% 0.025 250);
--line:oklch(28% 0.03 250);--line-soft:oklch(22% 0.025 250);
--accent:oklch(74% 0.14 60);--accent-2:oklch(65% 0.18 30);--accent-soft:oklch(74% 0.14 60 / 0.12);
--blue:#6ea8fe;--green:oklch(72% 0.15 150);--red:oklch(68% 0.17 25);--violet:#b89cff;
--maxw:1120px;
--font-display:"Fraunces","Iowan Old Style",Georgia,serif;
--font-body:"Inter",-apple-system,'Segoe UI',Roboto,system-ui,sans-serif;
--font-mono:"JetBrains Mono",ui-monospace,Consolas,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font-body);line-height:1.7;
-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;position:relative}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
background:radial-gradient(ellipse 70% 50% at 85% 3%,oklch(74% 0.14 60 / 0.06),transparent 60%),
 radial-gradient(ellipse 65% 40% at 5% 92%,oklch(55% 0.18 240 / 0.09),transparent 60%)}
body>*{position:relative;z-index:1}
.serif{font-family:var(--font-display);font-style:italic;font-weight:300}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.prose{max-width:72ch}
.prose p{margin:0 0 16px;font-size:17px;color:var(--ink-2)}
.prose p .lead-in{font-weight:600;color:var(--ink)}
#prog{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:60}
nav.top{position:sticky;top:0;z-index:50;background:oklch(12% 0.022 250 / 0.82);
backdrop-filter:saturate(140%) blur(14px);border-bottom:1px solid var(--line)}
nav.top .wrap{display:flex;gap:6px;align-items:center;height:54px;overflow-x:auto}
nav.top a{font-size:12.5px;color:var(--ink-2);text-decoration:none;padding:6px 10px;
border-radius:8px;white-space:nowrap;font-family:var(--font-mono);letter-spacing:.01em;
transition:background .2s,color .2s}
nav.top a:hover{background:var(--paper-3);color:var(--ink)}
nav.top .brand{font-family:var(--font-display);font-style:italic;font-weight:400;
font-size:16px;color:var(--ink);margin-right:10px;white-space:nowrap}
nav.top .langs{margin-left:auto;display:flex;gap:2px;flex-shrink:0}
nav.top .langs a{font-family:var(--font-mono);font-size:11px;letter-spacing:.06em;
padding:5px 10px;border-radius:999px;color:var(--mut)}
nav.top .langs a.on{background:var(--accent);color:oklch(18% 0.04 60);font-weight:600}
header.hero{padding:96px 0 70px;border-bottom:1px solid var(--line);position:relative;overflow:hidden}
header.hero::before{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
background:radial-gradient(ellipse 50% 60% at 82% 12%,oklch(74% 0.14 60 / 0.10),transparent 60%),
 radial-gradient(ellipse 45% 55% at 8% 80%,oklch(60% 0.18 240 / 0.10),transparent 60%)}
.kicker{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;
font-weight:500;color:var(--accent)}
header.hero h1{font-family:var(--font-display);font-style:italic;font-weight:300;
font-size:clamp(40px,7vw,76px);line-height:1.0;margin:16px 0 20px;letter-spacing:-.03em}
header.hero .thesis{font-size:20px;max-width:64ch;color:var(--ink-2);line-height:1.5}
header.hero .src{margin-top:24px;font-family:var(--font-mono);font-size:12px;color:var(--mut);letter-spacing:.01em;line-height:1.6}
.hero-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:44px;
border-top:1px solid var(--line)}
.hero-strip .hs{padding:20px 18px 6px;border-right:1px solid var(--line)}
.hero-strip .hs:last-child{border-right:0}
.hero-strip .v{font-family:var(--font-display);font-style:italic;font-weight:400;font-size:30px;
color:var(--accent);letter-spacing:-.02em}
.hero-strip .l{font-size:12.5px;color:var(--mut);margin-top:4px}
section{padding:72px 0}
section.alt{background:oklch(16% 0.027 250);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
section h2{font-family:var(--font-display);font-style:italic;font-weight:300;
font-size:clamp(28px,4vw,46px);line-height:1.06;margin:10px 0 10px;letter-spacing:-.025em}
.lede{font-size:19px;color:var(--ink-2);max-width:74ch;margin:0 0 26px;line-height:1.55}
.fig{background:var(--paper-2);border:1px solid var(--line);border-radius:16px;padding:14px 14px 6px;
margin:24px 0}
.figcap{font-family:var(--font-mono);font-size:12px;color:var(--mut);padding:6px 6px 10px;line-height:1.5}
.figcap b{color:var(--ink-2);font-weight:500}
.findings{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:8px 0 6px}
.stat{background:linear-gradient(180deg,var(--paper-2),var(--paper));border:1px solid var(--line);
border-left:3px solid var(--blue);border-radius:12px;padding:18px 20px}
.stat-v{font-family:var(--font-display);font-style:italic;font-weight:400;font-size:32px;letter-spacing:-.02em;color:var(--ink)}
.stat-l{font-size:14px;color:var(--ink);font-weight:500;margin-top:4px}
.stat-n{font-family:var(--font-mono);font-size:11.5px;color:var(--mut);margin-top:6px;line-height:1.45}
.tone-green{border-left-color:var(--green)}.tone-red{border-left-color:var(--red)}
.tone-amber{border-left-color:var(--accent)}.tone-violet{border-left-color:var(--violet)}
.tone-blue{border-left-color:var(--blue)}
.tone-ink{border-left-color:var(--ink-2)}
.tone-amber .stat-v,.tone-green .stat-v,.tone-red .stat-v,.tone-violet .stat-v{color:var(--accent)}
.tone-green .stat-v{color:var(--green)}.tone-red .stat-v{color:var(--red)}.tone-violet .stat-v{color:var(--violet)}
.tone-blue .stat-v{color:var(--blue)}
.callout{border-left:3px solid var(--accent);background:var(--accent-soft);padding:16px 22px;
border-radius:0 12px 12px 0;margin:26px 0;font-size:16.5px;color:var(--ink-2)}
.callout b{color:var(--ink)}
.pull{font-family:var(--font-display);font-style:italic;font-weight:300;font-size:27px;line-height:1.3;
color:var(--ink);border-top:1px solid var(--accent);border-bottom:1px solid var(--line);
padding:22px 0;margin:34px 0;max-width:34ch}
.grid2{display:grid;grid-template-columns:1.05fr .95fr;gap:36px;align-items:center}
@media(max-width:880px){.grid2{grid-template-columns:1fr}.hero-strip{grid-template-columns:repeat(2,1fr)}}
table.tbl{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:12px;
background:var(--paper-2);border:1px solid var(--line);border-radius:12px;overflow:hidden;
font-family:var(--font-mono)}
.tbl th,.tbl td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left}
.tbl th{background:var(--paper-3);color:var(--ink);font-weight:500;cursor:pointer;user-select:none;
position:sticky;top:54px;letter-spacing:.02em;text-transform:uppercase;font-size:11px}
.tbl td{color:var(--ink-2)}
.tbl td.num{text-align:right;font-variant-numeric:tabular-nums}
.tbl td.mono,.mono{font-family:var(--font-mono)}
.tbl td.mono{color:var(--accent)}
.tbl tr:hover td{background:var(--paper-3)}
.tbl .small{font-size:11px;color:var(--mut)}
footer{background:oklch(11% 0.02 250);color:var(--mut);padding:54px 0;font-size:13px;
border-top:1px solid var(--line);font-family:var(--font-mono);line-height:1.7}
footer b{font-family:var(--font-display);font-style:italic;font-weight:400;color:var(--ink);font-size:16px}
footer a{color:var(--blue)}
.dev-link{display:inline-flex;align-items:center;gap:8px;margin-top:16px;text-decoration:none;
color:var(--mut);font-family:var(--font-mono);font-size:12px;opacity:.8;transition:opacity .18s ease}
.dev-link:hover{opacity:1}.dev-link strong{color:var(--ink-2);font-weight:600}
.disc{font-size:12px;color:var(--mut);font-style:italic;margin-top:16px;font-family:var(--font-body)}
.refs{margin:10px 0 0;padding-left:22px;color:var(--ink-2);font-size:13.5px;line-height:1.65}
.refs li{margin-bottom:9px}.refs li b{color:var(--ink)}
.refs a{color:var(--blue);text-decoration:none}.refs a:hover{text-decoration:underline}
"""

PROG_JS = r"""
const prog=document.getElementById('prog');
addEventListener('scroll',()=>{const h=document.documentElement;
 const p=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;prog.style.width=p+'%';});
document.querySelectorAll('table.sortable th').forEach((th,i)=>{th.addEventListener('click',()=>{
 const tb=th.closest('table').querySelector('tbody');const rs=[...tb.querySelectorAll('tr')];
 const asc=th._a=!th._a;rs.sort((a,b)=>{const x=a.children[i].innerText.replace(/[^0-9,.\-]/g,'').replace(/\./g,'').replace(',','.');
 const y=b.children[i].innerText.replace(/[^0-9,.\-]/g,'').replace(/\./g,'').replace(',','.');
 const nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx;
 return asc?a.children[i].innerText.localeCompare(b.children[i].innerText):b.children[i].innerText.localeCompare(a.children[i].innerText);});
 rs.forEach(r=>tb.appendChild(r));});});
"""

STR_ALL = {
    "en": {
        "html_lang": "en",
        "title": "Rural Access Equity in Paraná",
        "meta_desc": ("Which of Paraná's municipalities are underserved by rural health, schools and "
                      "agricultural extension relative to their rural population. An Enhanced 2SFCA over "
                      "official IBGE, CNES, INEP and IDR-Paraná data, told as an interactive report."),
        "brand": "Rural Access Equity",
        "nav_coverage": "Coverage", "nav_map": "The map", "nav_services": "Three services",
        "nav_gaps": "The gaps", "nav_robust": "Robustness", "nav_method": "Method", "nav_table": "Ranking",
        # hero
        "hero_kicker": "Spatial equity · rural Paraná · Enhanced 2SFCA",
        "hero_title": "Rural Access Equity in Paraná",
        "hero_thesis": ("Health, schools and agricultural extension all promise universal rural coverage. "
                        "This report measures what that coverage is actually worth, municipality by "
                        "municipality, and finds a countryside that is not served evenly."),
        "hs1": "municipalities in the underserved bottom quintile",
        "hs2_v": "~1 in 4", "hs2": "of ranked rural residents live in that fifth ({bottom_pop})",
        "hs3": "service points geolocated across three networks",
        "hs4": "primary-care access gap, best vs worst fifth",
        "src": ("Source: IBGE Censo 2022 (SIDRA 9923), Ministério da Saúde (CNES), INEP Censo Escolar 2024, "
                "IDR-Paraná · {n_total} municipalities · Enhanced 2SFCA (Luo &amp; Qi 2009) · Own elaboration"),
        # coverage
        "co_kicker": "Coverage", "co_h2": "The countryside behind the coverage",
        "co_lede": ("About {rural_total} people, {rural_pct} of Paraná, live in the countryside and depend "
                    "on three public networks that are universal on paper."),
        "co_p1": ("<span class=\"lead-in\">Rural Paraná is not a small place.</span> {rural_total} people, "
                  "roughly {rural_pct} of the state's {pop_total} residents, live outside the urban grid, "
                  "spread across nearly 200,000 square kilometres of farmland, forest and river valley. They "
                  "rely on three parallel networks: primary care from the Sistema Único de Saúde, rural schools "
                  "from the public system, and agricultural extension from IDR-Paraná. Each network is meant to "
                  "reach everyone."),
        "co_p2": ("On paper, coverage is universal. In practice, a family in one municipality reaches a health "
                  "post in minutes while a family in the next faces a long drive over unpaved roads. This report "
                  "replaces the word covered with a number: for every municipality, how much service can its rural "
                  "population actually reach, and where do the shortfalls in health, schooling and extension line up."),
        "co_f1": "rural residents", "co_f1n": "{rural_pct} of Paraná's population",
        "co_f2": "primary-care facilities", "co_f2n": "CNES, Ministério da Saúde open-data API",
        "co_f3": "active rural schools", "co_f3n": "INEP Censo Escolar 2024",
        "co_f4": "extension offices", "co_f4n": "IDR-Paraná, extension units only",
        # map
        "mp_kicker": "The composite", "mp_h2": "One number per municipality",
        "mp_lede": ("Each municipality earns an access score for health, schools and extension, blended into a "
                    "single composite and ranked into quintiles. Use the buttons to switch surfaces."),
        "mp_cap": ("<b>Composite and per-service access percentiles.</b> Deep red is worse access, teal is "
                   "better. Switch between the composite and each service with the buttons. 0 = worst, 100 = "
                   "best. Municipalities with almost no rural population are left out of the ranking."),
        "mp_p1": ("The method is an Enhanced 2-Step Floating Catchment Area, the standard in the spatial-"
                  "accessibility literature. It credits a municipality for every facility its rural population can "
                  "reach within 50 km, discounts each facility by the competing demand around it, and lets "
                  "service spill across municipal borders the way real travel does. Each service becomes a "
                  "percentile, the three are averaged, and the bottom fifth is flagged as underserved."),
        "mp_pull": "Coverage is a promise. Access is a distance.",
        "m_composite": "Composite", "m_health": "Health", "m_education": "Schools",
        "m_extension": "Extension", "m_cbar": "Access pctile", "m_pctile": "Access percentile",
        # services
        "sv_kicker": "The surprise", "sv_h2": "Three services, three geographies",
        "sv_lede": ("The three networks do not overlap. Where primary care is strong, so is extension. Rural "
                    "schooling is the opposite."),
        "sv_cap": ("<b>Every ranked municipality, two relationships.</b> Green: health against extension access, "
                   "which rise together (r = {corr_hx}). Red: health against rural-school access, which pull "
                   "apart (r = {corr_he}). Lines are the fitted trends."),
        "sv_p1": ("Plot each municipality's health-access percentile against its extension-access percentile and "
                  "the cloud tilts clearly upward. The two rise together, at a correlation of {corr_hx}. That "
                  "makes sense: the health post and the extension office tend to sit in the same consolidated "
                  "towns of the north and the modernized agricultural belt."),
        "sv_p2": ("Swap extension for rural schools and the cloud flips. Health and schooling correlate at "
                  "{corr_he}, schooling against extension at {corr_ex}. Rural schools are densest exactly where "
                  "health and extension thin out, in the center-south. The composite is therefore not measuring "
                  "one thing. It is finding the places where two of the three networks fail at once."),
        "sv_callout": ("This is why the report shows the per-service maps next to the composite. A single "
                       "ranking would hide the fact that a municipality can be well served by schools and starved "
                       "of health and extension in the same breath. The underserved fifth is defined by that "
                       "double shortfall, not by any one service."),
        "cv_h": "Health", "cv_x": "Extension", "cv_e": "Schools",
        "cv_hx": "Health vs extension (r = {r})", "cv_he": "Health vs schools (r = {r})",
        "cv_xaxis": "Health access percentile", "cv_yaxis": "Extension / school access percentile",
        # gaps
        "gp_kicker": "The underserved fifth", "gp_h2": "Where the gaps stack up",
        "gp_lede": ("The bottom quintile is {bottom_n} municipalities holding {bottom_pop} rural residents, about "
                    "1 in 4 of the ranked countryside."),
        "gp_cap": ("<b>Access gap, best-served vs worst-served fifth.</b> Ratio of population-weighted raw "
                   "E2SFCA access between the top and bottom quintiles, per service. Higher means a steeper gap."),
        "gp_p1": ("The gap is widest for primary care: the best-served fifth reaches {gap_h} the per-capita "
                  "access of the worst-served fifth. Extension follows at {gap_x}. Rural schooling is nearly flat "
                  "at {gap_e}, the same story the scatter told. Schools are the one network that is relatively "
                  "even across the countryside, so they narrow the divide rather than widen it."),
        "gp_lede2": "Fifteen municipalities sit at the very bottom, led by {worst1}.",
        "gp_cap2": ("<b>The 15 lowest composite percentiles.</b> Colour marks the access quintile. Bars near "
                    "zero are the most underserved municipalities in the state."),
        "svc_health": "Primary care", "svc_extension": "Extension", "svc_education": "Rural schools",
        "gap_xaxis": "Access ratio, top vs bottom fifth (x)",
        "w_pctile": "Composite pctile", "w_pop": "Rural population", "w_xaxis": "Composite access percentile",
        # robustness
        "rb_kicker": "Robustness", "rb_h2": "How much to trust the ranking",
        "rb_lede": ("The composite weights the three services equally. Change the weights and watch how much "
                    "the underserved fifth moves."),
        "rb_cap": ("<b>Stability of the bottom quintile under alternative weightings.</b> Share of the equal-"
                   "weight Q1 municipalities that stay in Q1 when the weights tilt toward one service, or follow the "
                   "first principal component."),
        "rb_p1": ("Tilt the weights toward health, and the underserved fifth barely changes: {ov_health} of it "
                  "stays put, and extension behaves the same way, because those two networks move together. Tilt "
                  "toward rural schools instead and only {ov_education} survives, because schooling pulls against "
                  "the other two. A data-driven principal-component weighting keeps just {ov_pc1}. The honest "
                  "reading is moderate robustness: the ranking is stable as long as it is not driven by the one "
                  "network that runs the other way, and that tension is a finding worth showing rather than "
                  "smoothing over."),
        "sc_equal": "Equal", "sc_health": "Health-heavy", "sc_extension": "Extension-heavy",
        "sc_education": "School-heavy", "sc_pc1": "PC1-derived",
        "sc_yaxis": "Q1 overlap with equal weights (%)",
        # method
        "mt_kicker": "Method", "mt_h2": "How it is built",
        "mt_lede": "Four official datasets, one accessibility formula, one command.",
        "mt_p1": ("The pipeline pulls {cnes} primary-care facilities live from the Ministério da Saúde open-"
                  "data API, {inep} rural schools from the INEP Censo Escolar 2024, {ater} extension offices from "
                  "the IDR-Paraná unit shapefile, and rural population from the 2022 Census (IBGE SIDRA 9923). "
                  "Access is scored with an Enhanced 2-Step Floating Catchment Area (Luo and Qi, 2009): great-"
                  "circle distance, Gaussian decay with a 30 km bandwidth, a 50 km catchment cutoff, and an "
                  "equal-weight composite of per-service percentile ranks."),
        "mt_p2": ("Every source caches to disk and the whole report rebuilds from raw data with a single "
                  "command. The code, the methodology write-up and the interactive map are open source. Known "
                  "limitations, namely great-circle rather than travel-time distance, border effects along the "
                  "Itaipu reservoir, and schools anchored to municipal centroids because the 2024 microdata "
                  "dropped coordinates, are documented in full in the repository."),
        "mt_refs_h": "Selected references",
        "mt_disc": ("An independent portfolio study by Avner Paes Gomes. Not affiliated with IBGE, the "
                    "Ministério da Saúde, INEP or IDR-Paraná."),
        # table
        "tb_kicker": "The full ranking", "tb_h2": "Municipality by municipality",
        "tb_lede": "Every ranked municipality, sortable. Click a column header to reorder.",
        "th_muni": "Municipality", "th_pop": "Rural pop.", "th_health": "Health", "th_education": "Schools",
        "th_extension": "Extension", "th_composite": "Composite", "th_quintile": "Quintile",
        # footer
        "ft_by": "Developed by",
        "ft_body": ("Paraná Rural Access Equity · Enhanced 2SFCA over IBGE, CNES, INEP and IDR-Paraná open "
                    "data · {n_ranked} municipalities ranked · Full pipeline and methodology open source."),
    },
    "pt": {
        "html_lang": "pt-br",
        "title": "Equidade no Acesso Rural no Paraná",
        "meta_desc": ("Quais municípios do Paraná são menos servidos por saúde, escola e extensão rural em "
                      "relação à sua população rural. Um Enhanced 2SFCA sobre dados oficiais do IBGE, CNES, INEP "
                      "e IDR-Paraná, contado como um relatório interativo."),
        "brand": "Equidade no Acesso Rural",
        "nav_coverage": "Cobertura", "nav_map": "O mapa", "nav_services": "Três serviços",
        "nav_gaps": "As lacunas", "nav_robust": "Robustez", "nav_method": "Método", "nav_table": "Ranking",
        # hero
        "hero_kicker": "Equidade espacial · Paraná rural · Enhanced 2SFCA",
        "hero_title": "Equidade no Acesso Rural no Paraná",
        "hero_thesis": ("Saúde, escola e extensão rural prometem cobertura universal no campo. Este relatório "
                        "mede quanto essa cobertura vale de fato, município a município, e encontra um campo "
                        "que não é atendido de forma uniforme."),
        "hs1": "municípios no quintil inferior, os subatendidos",
        "hs2_v": "~1 em 4", "hs2": "da população rural ranqueada vive nesse quinto ({bottom_pop})",
        "hs3": "pontos de serviço georreferenciados em três redes",
        "hs4": "diferença de acesso à atenção primária, melhor vs pior quinto",
        "src": ("Fonte: IBGE Censo 2022 (SIDRA 9923), Ministério da Saúde (CNES), INEP Censo Escolar 2024, "
                "IDR-Paraná · {n_total} municípios · Enhanced 2SFCA (Luo &amp; Qi 2009) · Elaboração própria"),
        # coverage
        "co_kicker": "Cobertura", "co_h2": "O campo por trás da cobertura",
        "co_lede": ("Cerca de {rural_total} pessoas, {rural_pct} do Paraná, vivem no campo e dependem de três "
                    "redes públicas que são universais no papel."),
        "co_p1": ("<span class=\"lead-in\">O Paraná rural não é pouca coisa.</span> São {rural_total} pessoas, "
                  "cerca de {rural_pct} dos {pop_total} habitantes do estado, vivendo fora da malha urbana, "
                  "espalhadas por quase 200 mil quilômetros quadrados de lavoura, floresta e vale de rio. Elas "
                  "dependem de três redes paralelas: atenção primária pelo Sistema Único de Saúde, escolas "
                  "rurais pela rede pública e extensão rural pelo IDR-Paraná. Cada rede deveria alcançar todos."),
        "co_p2": ("No papel, a cobertura é universal. Na prática, uma família de um município chega a uma UBS "
                  "em minutos enquanto a do município vizinho enfrenta uma longa estrada de chão. Este relatório "
                  "troca a palavra coberto por um número: para cada município, quanto serviço a sua população "
                  "rural realmente alcança, e onde as lacunas de saúde, escola e extensão se sobrepõem."),
        "co_f1": "residentes rurais", "co_f1n": "{rural_pct} da população do Paraná",
        "co_f2": "estabelecimentos de atenção primária", "co_f2n": "CNES, API de dados abertos do MS",
        "co_f3": "escolas rurais ativas", "co_f3n": "INEP Censo Escolar 2024",
        "co_f4": "unidades de extensão", "co_f4n": "IDR-Paraná, só unidades de extensão",
        # map
        "mp_kicker": "O composto", "mp_h2": "Um número por município",
        "mp_lede": ("Cada município ganha um escore de acesso à saúde, escola e extensão, combinado num único "
                    "composto e ranqueado em quintis. Use os botões para trocar de camada."),
        "mp_cap": ("<b>Percentis de acesso, composto e por serviço.</b> Vermelho escuro é pior acesso, verde-"
                   "água é melhor. Troque entre o composto e cada serviço pelos botões. 0 = pior, 100 = melhor. "
                   "Municípios quase sem população rural ficam fora do ranking."),
        "mp_p1": ("O método é um Enhanced 2-Step Floating Catchment Area, padrão na literatura de "
                  "acessibilidade espacial. Ele credita ao município cada equipamento que sua população rural "
                  "alcança em 50 km, desconta cada equipamento pela demanda que disputa em volta, e deixa o "
                  "serviço atravessar as divisas municipais como o deslocamento real faz. Cada serviço vira um "
                  "percentil, os três viram uma média, e o quinto inferior é marcado como subatendido."),
        "mp_pull": "Cobertura é uma promessa. Acesso é uma distância.",
        "m_composite": "Composto", "m_health": "Saúde", "m_education": "Escolas",
        "m_extension": "Extensão", "m_cbar": "Percentil", "m_pctile": "Percentil de acesso",
        # services
        "sv_kicker": "A surpresa", "sv_h2": "Três serviços, três geografias",
        "sv_lede": ("As três redes não se sobrepõem. Onde a atenção primária é forte, a extensão também é. A "
                    "escola rural é o oposto."),
        "sv_cap": ("<b>Cada município ranqueado, duas relações.</b> Verde: acesso à saúde contra acesso à "
                   "extensão, que sobem juntos (r = {corr_hx}). Vermelho: saúde contra acesso à escola rural, que "
                   "se afastam (r = {corr_he}). As linhas são as tendências ajustadas."),
        "sv_p1": ("Cruze o percentil de acesso à saúde de cada município com o de acesso à extensão e a nuvem "
                  "sobe com clareza. Os dois crescem juntos, com correlação de {corr_hx}. Faz sentido: a UBS e o "
                  "escritório de extensão tendem a ficar nas mesmas cidades consolidadas do norte e do cinturão "
                  "agrícola modernizado."),
        "sv_p2": ("Troque extensão por escola rural e a nuvem se inverte. Saúde e escola se correlacionam em "
                  "{corr_he}, e escola contra extensão em {corr_ex}. As escolas rurais são mais densas exatamente "
                  "onde saúde e extensão rareiam, no centro-sul. O composto, portanto, não mede uma coisa só. Ele "
                  "encontra os lugares onde duas das três redes falham ao mesmo tempo."),
        "sv_callout": ("É por isso que o relatório mostra os mapas por serviço ao lado do composto. Um ranking "
                       "único esconderia que um município pode ser bem servido por escolas e carente de saúde e "
                       "extensão no mesmo fôlego. O quinto subatendido é definido por essa lacuna dupla, não por "
                       "um serviço isolado."),
        "cv_h": "Saúde", "cv_x": "Extensão", "cv_e": "Escolas",
        "cv_hx": "Saúde vs extensão (r = {r})", "cv_he": "Saúde vs escolas (r = {r})",
        "cv_xaxis": "Percentil de acesso à saúde", "cv_yaxis": "Percentil de acesso, extensão / escola",
        # gaps
        "gp_kicker": "O quinto subatendido", "gp_h2": "Onde as lacunas se acumulam",
        "gp_lede": ("O quintil inferior são {bottom_n} municípios que concentram {bottom_pop} residentes "
                    "rurais, cerca de 1 em cada 4 do campo ranqueado."),
        "gp_cap": ("<b>Diferença de acesso, melhor quinto vs pior quinto.</b> Razão do acesso bruto E2SFCA "
                   "ponderado por população entre o quintil superior e o inferior, por serviço. Maior significa "
                   "diferença mais acentuada."),
        "gp_p1": ("A diferença é maior na atenção primária: o quinto mais bem servido alcança {gap_h} o acesso "
                  "per capita do pior quinto. A extensão vem logo atrás, em {gap_x}. A escola rural é quase plana, "
                  "em {gap_e}, a mesma história que o gráfico de dispersão contou. A escola é a única rede "
                  "relativamente uniforme no campo, então ela estreita a divisão em vez de alargá-la."),
        "gp_lede2": "Quinze municípios ficam bem no fundo, encabeçados por {worst1}.",
        "gp_cap2": ("<b>Os 15 menores percentis compostos.</b> A cor marca o quintil de acesso. Barras perto "
                    "de zero são os municípios mais subatendidos do estado."),
        "svc_health": "Atenção primária", "svc_extension": "Extensão", "svc_education": "Escola rural",
        "gap_xaxis": "Razão de acesso, quinto superior vs inferior (x)",
        "w_pctile": "Percentil composto", "w_pop": "População rural", "w_xaxis": "Percentil de acesso composto",
        # robustness
        "rb_kicker": "Robustez", "rb_h2": "Quanto confiar no ranking",
        "rb_lede": ("O composto pesa os três serviços igualmente. Mude os pesos e veja quanto o quinto "
                    "subatendido se mexe."),
        "rb_cap": ("<b>Estabilidade do quintil inferior sob pesos alternativos.</b> Fração dos municípios do "
                   "Q1 com pesos iguais que continuam no Q1 quando os pesos pendem para um serviço, ou seguem o "
                   "primeiro componente principal."),
        "rb_p1": ("Incline os pesos para a saúde e o quinto subatendido quase não muda: {ov_health} dele "
                  "permanece, e a extensão se comporta do mesmo jeito, porque essas duas redes andam juntas. "
                  "Incline para a escola rural e apenas {ov_education} sobrevive, porque a escola puxa contra as "
                  "outras duas. Uma ponderação por componente principal mantém só {ov_pc1}. A leitura honesta é "
                  "robustez moderada: o ranking é estável enquanto não for guiado pela única rede que corre no "
                  "sentido contrário, e essa tensão é um achado que vale mostrar em vez de disfarçar."),
        "sc_equal": "Iguais", "sc_health": "Pró-saúde", "sc_extension": "Pró-extensão",
        "sc_education": "Pró-escola", "sc_pc1": "Por PC1",
        "sc_yaxis": "Sobreposição com pesos iguais (%)",
        # method
        "mt_kicker": "Método", "mt_h2": "Como é construído",
        "mt_lede": "Quatro bases oficiais, uma fórmula de acessibilidade, um comando.",
        "mt_p1": ("O pipeline puxa {cnes} estabelecimentos de atenção primária ao vivo da API de dados abertos "
                  "do Ministério da Saúde, {inep} escolas rurais do INEP Censo Escolar 2024, {ater} unidades de "
                  "extensão do shapefile de unidades do IDR-Paraná, e a população rural do Censo 2022 (IBGE SIDRA "
                  "9923). O acesso é medido por um Enhanced 2-Step Floating Catchment Area (Luo e Qi, 2009): "
                  "distância em linha reta, decaimento gaussiano com banda de 30 km, corte de captação em 50 km "
                  "e um composto de pesos iguais dos percentis por serviço."),
        "mt_p2": ("Cada fonte vai para cache em disco e o relatório inteiro se reconstrói a partir do dado "
                  "bruto com um único comando. O código, o texto de metodologia e o mapa interativo são abertos. "
                  "As limitações conhecidas, a saber distância em linha reta em vez de tempo de viagem, efeitos "
                  "de borda no reservatório de Itaipu, e escolas ancoradas no centroide municipal porque o "
                  "microdado de 2024 deixou de trazer coordenadas, estão documentadas por completo no repositório."),
        "mt_refs_h": "Referências selecionadas",
        "mt_disc": ("Estudo de portfólio independente de Avner Paes Gomes. Sem vínculo com IBGE, Ministério da "
                    "Saúde, INEP ou IDR-Paraná."),
        # table
        "tb_kicker": "O ranking completo", "tb_h2": "Município a município",
        "tb_lede": "Cada município ranqueado, ordenável. Clique no cabeçalho de uma coluna.",
        "th_muni": "Município", "th_pop": "Pop. rural", "th_health": "Saúde", "th_education": "Escolas",
        "th_extension": "Extensão", "th_composite": "Composto", "th_quintile": "Quintil",
        # footer
        "ft_by": "Desenvolvido por",
        "ft_body": ("Equidade no Acesso Rural no Paraná · Enhanced 2SFCA sobre dados abertos do IBGE, CNES, "
                    "INEP e IDR-Paraná · {n_ranked} municípios ranqueados · Pipeline e metodologia abertos."),
    },
}
