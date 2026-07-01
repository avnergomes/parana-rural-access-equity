# O acesso a serviços rurais não é uniforme no Paraná

_Quais dos 399 municípios paranaenses são menos servidos por saúde, educação e extensão rural em relação à sua população rural?_

## A pergunta

O Paraná rural tem cerca de 1,26 milhão de pessoas, 11% dos 11,4 milhões do estado, espalhadas por cerca de 200 mil km². Elas dependem de três redes paralelas de serviços: atenção primária do Ministério da Saúde (UBS via CNES), escolas rurais do INEP e extensão rural do IDR-Paraná. Cobertura universal, no papel. Na prática, moradores rurais de alguns municípios enfrentam uma longa estrada até a UBS mais próxima; outros vivem a poucos quilômetros. Este projeto quantifica essa distância.

## O que eu fiz

Construí um pipeline reprodutível que:

1. Baixou os 399 polígonos municipais paranaenses e a população rural do Censo 2022 (IBGE SIDRA tabela 9923).
2. Baixou todos os estabelecimentos de atenção básica no CNES (`codigo_tipo_unidade ∈ {1, 2, 32, 40}`: postos, UBS, unidades móveis) via a API de dados abertos do Ministério da Saúde. São 3.075 estabelecimentos com coordenadas válidas.
3. Baixou todas as escolas ativas rurais e diferenciadas do INEP Censo Escolar 2024 (`TP_LOCALIZACAO == 2` OR `TP_LOCALIZACAO_DIFERENCIADA > 0`): 1.187 escolas no estado.
4. Carregou os 22 Núcleos Regionais do IDR-Paraná via um CSV curado.
5. Calculou um **Enhanced 2-Step Floating Catchment Area** (Luo & Qi, 2009) por serviço, com decaimento gaussiano da distância (β = 30 km) e cutoff de captação em 50 km.
6. Converteu cada escore por serviço em ranking percentil e tirou a média com pesos iguais para o índice composto.
7. Rankeou os 364 municípios com população rural relevante em quintis; marca-se o quintil inferior como "subatendido".

Tudo em Python. Todo dataset bruto vai para cache em disco. O pipeline inteiro roda em cerca de 20 minutos num laptop.

## Achados principais

- **Quintil inferior (Q1):** 73 municípios. Concentram-se no interior do Centro-Sul e dos Campos Gerais (Tibagi, Candói, Altamira do Paraná, Nova Cantu), na divisa do Norte Pioneiro (Santana e Salto do Itararé) e num grupo de pequenos municípios da Costa Oeste espremidos contra o reservatório de Itaipu (Pato Bragado, Santa Helena, Mercedes, Entre Rios do Oeste).
- **Impacto populacional:** 196.356 residentes rurais, cerca de 1 em cada 6 da população rural ranqueada do estado, vivem num município do Q1.
- **Gap de acesso:** no quintil mais mal servido, o acesso bruto per capita (E2SFCA, ponderado por população) é cerca de 2,2x menor que no melhor quintil para atenção primária e cerca de 2,3x menor para escola rural. A extensão mostra um gap bem maior, mas esse número é dominado pela baixa resolução da camada de ATER (22 pontos) e deve ser lido como ressalva, não manchete.
- **Robustez:** o Q1 é moderadamente estável quando os pesos pendem para um único serviço: 67 a 88% dos municípios do Q1 permanecem no Q1 sob esquemas pró-saúde, pró-educação ou anti-extensão. Ele *não* é estável sob uma ponderação derivada de PC1 (27% de sobreposição), e esse é o ponto interessante. Saúde e escola rural são espacialmente anti-correlacionadas no Paraná (o norte é forte em atenção primária, o centro-sul em escolas rurais), então o primeiro componente principal captura essa tensão em vez de um eixo comum de acesso. Reporto os mapas por serviço ao lado do composto exatamente por isso.

## Por que essa formulação

Eu poderia ter contado UBS por 5.000 residentes rurais e parado por aí. Seria enganoso. A métrica ingênua "instalações per capita" ignora que uma UBS 3 km fora do limite municipal ainda atende aquela população, e trata as divisas municipais como impermeáveis. O E2SFCA captura os dois efeitos e é o padrão atual na literatura brasileira de geografia da saúde. A justificativa metodológica completa, referências e checagens de robustez estão em `docs/METHODOLOGY.md`.

Pesos iguais entre os três serviços refletem o enquadramento constitucional (Art. 196 saúde; Art. 205 educação; Lei 12.188/2010 PNATER extensão). Reporto a sensibilidade ao peso como checagem de robustez em vez de fingir que uma ponderação específica é objetivamente correta.

## Limitações que quero corrigir numa v2

- **Distâncias em linha reta** ignoram o relevo (Serra do Mar, Serra Geral). Uma v2 com isócronas na malha viária OSM (osmnx com PBFs pré-recortados por município) apertaria o escore de saúde no Litoral Norte e Vale do Ribeira em especial.
- **Efeitos de borda** puxam para baixo os pequenos municípios da Costa Oeste no reservatório de Itaipu: a captação de 50 km é cortada pela água e pela fronteira internacional, e estabelecimentos paraguaios do outro lado não contam. É geografia real, mas uma captação nacional com borda suavizaria o efeito.
- **Capacidade CNES = 1 unidade por estabelecimento** subestima UBS mais movimentadas com várias equipes de Saúde da Família. Juntar as tabelas `EQ` do CNES resolve.
- **Escolas do INEP ancoradas no centroide municipal.** O microdado do Censo Escolar 2024 não publica mais coordenadas das escolas, então cada escola é posicionada no centroide do seu município. Isso combina com a resolução municipal da análise, mas perde o detalhe intramunicipal; uma v2 juntaria o "Catálogo de Escolas" do INEP para pontos reais.
- **A camada de ATER é grosseira:** 22 Núcleos Regionais representam toda a rede de extensão, e por isso o gap de acesso à extensão é grande e volátil. Localizar as unidades municipais de ATER refinaria isso.
- **Instalações fora do estado** são ignoradas. Municípios fronteiriços com SP, SC e MS teriam escores um pouco melhores com uma captação em escala nacional.

## O que essa peça mostra

O mapa é a superfície. Embaixo está um pipeline geoespacial reprodutível que ingere três bases federais, aplica uma fórmula de acessibilidade revisada por pares, normaliza para um resumo compartilhável e produz tanto um choropleth estático em qualidade de portfolio quanto um mapa interativo em Folium. Todo parâmetro está em `src/config.py`. Toda fonte tem versão. O `Makefile` reproduz tudo do zero em uma linha.

O repositório `parana-rural-access-equity` é um fim de semana de trabalho. O padrão (dados públicos, E2SFCA, ranking percentil, choropleth em quintis, writeup bilíngue) generaliza para qualquer região dos EUA ou da Europa. Basta trocar IBGE por TIGER/Line + ACS, CNES por registros estaduais de saúde, INEP por diretórios estaduais de educação. O pipeline é o pedaço de portfolio.

**Repositório:** `github.com/avnergomes/parana-rural-access-equity`
**Mapa interativo:** `avnergomes.github.io/parana-rural-access-equity/`
**Metodologia + referências:** [`docs/METHODOLOGY.md`](METHODOLOGY.md)
**Contato:** Avner Paes Gomes · avnerpaesgomes@gmail.com · [LinkedIn](https://linkedin.com/in/avnergomes)
