# LinkedIn drafts

Two hook framings each (impact vs method). Pick one PT and one EN for launch; keep the alternate for a follow-up two weeks later. All statistics get double-checked against `output/headline_stats.json` before posting.

**Voice rules (Avner):** no em-dashes, no hashtags, no closing questions, no emoji bullets. Punchy first two lines. Public repo + interactive report linked at the end.

---

## English

### Hook A: impact framing (recommended launch)

About 1 in 4 rural Paranaenses lives in a municipality that ranks in the bottom quintile of composite access to health, education, and agricultural extension services. That is 73 municipalities and 338,499 rural residents.

I mapped every municipality of Paraná using an Enhanced 2-Step Floating Catchment Area over three federal datasets: 3,075 primary-care facilities from CNES, 1,187 rural schools from INEP, and 414 georeferenced IDR-Paraná extension offices from the official IDR unit shapefile.

What it produces:
- One reproducible Python pipeline (make all, run in 20 min)
- A composite E2SFCA percentile per municipality
- An interactive report (PT and EN) with a switchable map, the co-variation chart, and a sortable municipality ranking
- A short methodology writeup with the citations

In the worst-served fifth, per-capita access to primary care runs about 3.3 times below the best-served fifth, and extension access about 2.9 times below, while rural schooling sits only 1.2 times below. Health and extension move together, concentrating in the same more-developed municipalities of the north and the modernized agricultural belt. Rural-school access is the mirror image, strongest in the center-south. So the composite's worst-off fifth is where health and extension are both thin at once, and those places tend to have relatively more rural schools.

The pattern generalizes. Swap IBGE for TIGER/Line + ACS and it becomes a US spatial-equity script.

Interactive report: avnergomes.github.io/parana-rural-access-equity/parana_access_report_en.html
Repo: github.com/avnergomes/parana-rural-access-equity

### Hook B: method framing (follow-up two weeks later)

Weekend build: an Enhanced 2-Step Floating Catchment Area (Luo and Qi, 2009) across every municipality of Paraná, Brazil.

- Demand: rural population per municipality from IBGE Censo 2022 (SIDRA 9923)
- Supply: 3,075 primary-care CNES facilities, 1,187 INEP rural schools, 414 IDR-Paraná extension offices from the official unit shapefile
- Distance: haversine, Gaussian decay, beta = 30 km, d0 = 50 km catchment
- Composite: equal-weight average of per-service percentile ranks
- Robustness: the bottom quintile keeps 92 percent of its members under a health-heavy tilt and 80 percent under an extension-heavy tilt, but only 56 percent when I reweight toward education, so I publish the per-service maps next to the composite

One nice surprise from the data: primary-care access and extension access move together (correlation +0.74), while rural-school access is the mirror image (education is anti-correlated with both, -0.46 against health and -0.73 against extension). Health and extension concentrate in the north and the modernized agricultural belt; rural schools are strongest in the center-south. The composite finds the places where health and extension run thin at the same time.

Every parameter is in src/config.py. The Makefile reproduces from scratch in one line. The whole story is a self-contained interactive report, PT and EN.

Interactive report: avnergomes.github.io/parana-rural-access-equity/parana_access_report_en.html
Repo: github.com/avnergomes/parana-rural-access-equity

---

## Português

### Hook A: enquadramento de impacto (lançamento recomendado)

Cerca de 1 em cada 4 paranaenses da zona rural vive num município no quintil inferior de acesso composto a saúde, educação e ATER. São 73 municípios e 338.499 residentes rurais.

Mapeei todos os municípios do Paraná com um Enhanced 2-Step Floating Catchment Area sobre três bases federais: 3.075 estabelecimentos de atenção primária no CNES, 1.187 escolas rurais no INEP e 414 unidades de extensão georreferenciadas do IDR-Paraná, extraídas do shapefile oficial de unidades.

O que sai:
- Pipeline Python reprodutível (make all, roda em 20 min)
- E2SFCA composto em percentil por município
- Um relatório interativo (PT e EN) com mapa comutável, o gráfico de co-variação e um ranking ordenável por município
- Writeup metodológico curto com as referências

No quintil mais mal servido, o acesso per capita à atenção primária fica cerca de 3,3x abaixo do melhor quintil, e a extensão cerca de 2,9x abaixo, enquanto a escola rural fica só 1,2x abaixo. Saúde e extensão andam juntas, concentrando-se nos mesmos municípios mais desenvolvidos do norte e do cinturão agrícola modernizado. O acesso à escola rural é o espelho, mais forte no centro-sul. Então o quintil mais mal servido do composto é onde saúde e extensão estão fracas ao mesmo tempo, e esses lugares tendem a ter relativamente mais escolas rurais.

O padrão generaliza. Trocando IBGE por TIGER/Line + ACS o mesmo script vira uma análise de equidade espacial para qualquer região dos EUA.

Relatório interativo: avnergomes.github.io/parana-rural-access-equity/parana_access_report_pt.html
Repositório: github.com/avnergomes/parana-rural-access-equity

### Hook B: enquadramento metodológico (follow-up duas semanas depois)

Fim de semana: Enhanced 2-Step Floating Catchment Area (Luo e Qi, 2009) para os municípios do Paraná.

- Demanda: população rural por município do Censo 2022 (SIDRA 9923)
- Oferta: 3.075 estabelecimentos de atenção primária CNES, 1.187 escolas rurais INEP, 414 unidades de extensão IDR-Paraná do shapefile oficial de unidades
- Distância: haversine, decaimento gaussiano, beta = 30 km, d0 = 50 km
- Composto: média com pesos iguais de percentis por serviço
- Robustez: o quintil inferior mantém 92% dos membros num peso maior para saúde e 80% num peso maior para extensão, mas só 56% quando reforço a educação, então publico os mapas por serviço ao lado do composto

Uma surpresa boa dos dados: acesso à atenção primária e acesso à extensão andam juntos (correlação +0,74), enquanto o acesso à escola rural é o espelho (a educação é anti-correlacionada com os dois, -0,46 contra saúde e -0,73 contra extensão). Saúde e extensão se concentram no norte e no cinturão agrícola modernizado; as escolas rurais são mais fortes no centro-sul. O composto encontra os lugares onde saúde e extensão estão fracas ao mesmo tempo.

Todo parâmetro em src/config.py. O Makefile reproduz tudo do zero em uma linha. A história inteira está num relatório interativo self-contained, PT e EN.

Relatório interativo: avnergomes.github.io/parana-rural-access-equity/parana_access_report_pt.html
Repositório: github.com/avnergomes/parana-rural-access-equity

---

## Links (both editions)

- Interactive report EN: avnergomes.github.io/parana-rural-access-equity/parana_access_report_en.html
- Relatório interativo PT: avnergomes.github.io/parana-rural-access-equity/parana_access_report_pt.html
- Portfolio article: avnergomes.github.io/portfolio/articles/parana-rural-access-equity.html
- Repo: github.com/avnergomes/parana-rural-access-equity

---

## Pre-publish checklist

- [ ] Sanity-check every hard-coded stat against `output/headline_stats.json` (bottom quintile count, population share, gap ratio).
- [ ] Confirm the interactive report renders on mobile (PT and EN).
- [ ] Attach `output/choropleth_access_score.png` as the card image.
- [ ] Tag: no hashtags; mention `linkedin.com/in/luowei` if the E2SFCA authorship is a natural nod (only if it feels organic).
- [ ] Post window: 08:30-09:30 or 12:00-13:30 BRT (Avner's audience is warmest then).
