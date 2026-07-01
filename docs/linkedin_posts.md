# LinkedIn drafts

Two hook framings each (impact vs method). Pick one PT and one EN for launch; keep the alternate for a follow-up two weeks later. All statistics get double-checked against `output/headline_stats.json` before posting.

**Voice rules (Avner):** no em-dashes, no hashtags, no closing questions, no emoji bullets. Punchy first two lines. Public repo + live map linked at the end.

---

## English

### Hook A: impact framing (recommended launch)

About 1 in 6 rural Paranaenses lives in a município that ranks in the bottom quintile of composite access to health, education, and agricultural extension services. That is 73 municipalities and 196,356 rural residents.

I mapped every município of Paraná using an Enhanced 2-Step Floating Catchment Area over three federal datasets: 3,075 primary-care facilities from CNES, 1,187 rural schools from INEP, and the 22 IDR-Paraná regional extension offices.

What it produces:
- One reproducible Python pipeline (make all, run in 20 min)
- A composite E2SFCA percentile per município
- A choropleth PNG and a Folium interactive map
- A short methodology writeup with the citations

In the worst-served fifth, per-capita access to primary care and rural schooling runs about 2.2 to 2.3 times below the best-served fifth. And the two do not move together: the north is strong on health, the center-south on rural schools, so the composite is really a story about where both are thin at once.

The pattern generalizes. Swap IBGE for TIGER/Line + ACS and it becomes a US spatial-equity script.

Repo: github.com/avnergomes/parana-rural-access-equity
Live map: avnergomes.github.io/parana-rural-access-equity

### Hook B: method framing (follow-up two weeks later)

Weekend build: an Enhanced 2-Step Floating Catchment Area (Luo and Qi, 2009) across every municipality of Paraná, Brazil.

- Demand: rural population per município from IBGE Censo 2022 (SIDRA 9923)
- Supply: 3,075 primary-care CNES facilities, 1,187 INEP rural schools, 22 IDR-Paraná extension offices
- Distance: haversine, Gaussian decay, beta = 30 km, d0 = 50 km catchment
- Composite: equal-weight average of per-service percentile ranks
- Robustness: the bottom quintile holds 67 to 88 percent of its members when I tilt the weights toward any single service, but health and schooling are spatially anti-correlated, so I report the per-service maps next to the composite

One nice surprise from the data: primary-care access and rural-school access do not overlap. The north of the state is strong on health, the center-south on schools. The composite finds the places where both run thin at the same time.

Every parameter is in src/config.py. The Makefile reproduces from scratch in one line. Bilingual PT + EN write-up in the repo.

Repo: github.com/avnergomes/parana-rural-access-equity

---

## Português

### Hook A: enquadramento de impacto (lançamento recomendado)

Cerca de 1 em cada 6 paranaenses da zona rural vive num município no quintil inferior de acesso composto a saúde, educação e ATER. São 73 municípios e 196.356 residentes rurais.

Mapeei todos os municípios do Paraná com um Enhanced 2-Step Floating Catchment Area sobre três bases federais: 3.075 estabelecimentos de atenção primária no CNES, 1.187 escolas rurais no INEP e os 22 Núcleos Regionais do IDR-Paraná.

O que sai:
- Pipeline Python reprodutível (make all, roda em 20 min)
- E2SFCA composto em percentil por município
- Choropleth em PNG e mapa interativo em Folium
- Writeup metodológico curto com as referências

No quintil mais mal servido, o acesso per capita a atenção primária e a escola rural fica cerca de 2,2 a 2,3x abaixo do melhor quintil. E os dois não andam juntos: o norte é forte em saúde, o centro-sul em escolas rurais, então o composto acaba mostrando onde as duas redes estão fracas ao mesmo tempo.

O padrão generaliza. Trocando IBGE por TIGER/Line + ACS o mesmo script vira uma análise de equidade espacial para qualquer região dos EUA.

Repositório: github.com/avnergomes/parana-rural-access-equity
Mapa interativo: avnergomes.github.io/parana-rural-access-equity

### Hook B: enquadramento metodológico (follow-up duas semanas depois)

Fim de semana: Enhanced 2-Step Floating Catchment Area (Luo e Qi, 2009) para os municípios do Paraná.

- Demanda: população rural por município do Censo 2022 (SIDRA 9923)
- Oferta: 3.075 estabelecimentos de atenção primária CNES, 1.187 escolas rurais INEP, 22 Núcleos Regionais IDR-Paraná
- Distância: haversine, decaimento gaussiano, beta = 30 km, d0 = 50 km
- Composto: média com pesos iguais de percentis por serviço
- Robustez: o quintil inferior mantém 67 a 88% dos membros quando inclino os pesos para um único serviço, mas saúde e escola são espacialmente anti-correlacionadas, então reporto os mapas por serviço ao lado do composto

Uma surpresa boa dos dados: acesso a atenção primária e acesso a escola rural não coincidem. O norte do estado é forte em saúde, o centro-sul em escolas. O composto encontra os lugares onde as duas redes estão fracas ao mesmo tempo.

Todo parâmetro em src/config.py. O Makefile reproduz tudo do zero em uma linha. Writeup bilíngue PT + EN no repositório.

Repositório: github.com/avnergomes/parana-rural-access-equity

---

## Pre-publish checklist

- [ ] Sanity-check every hard-coded stat against `output/headline_stats.json` (bottom quintile count, population share, gap ratio).
- [ ] Confirm the live map URL renders on mobile.
- [ ] Attach `output/choropleth_access_score.png` as the card image.
- [ ] Tag: no hashtags; mention `linkedin.com/in/luowei` if the E2SFCA authorship is a natural nod (only if it feels organic).
- [ ] Post window: 08:30-09:30 or 12:00-13:30 BRT (Avner's audience is warmest then).
