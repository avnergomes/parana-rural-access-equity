# O acesso a serviços rurais não é uniforme no Paraná

_Quais dos 399 municípios paranaenses são menos servidos por saúde, educação e extensão rural em relação à sua população rural?_

## A pergunta

O Paraná rural tem cerca de 1,26 milhão de pessoas, 11% dos 11,4 milhões do estado, espalhadas por cerca de 200 mil km². Elas dependem de três redes paralelas de serviços: atenção primária do Ministério da Saúde (UBS via CNES), escolas rurais do INEP e extensão rural do IDR-Paraná. Cobertura universal, no papel. Na prática, moradores rurais de alguns municípios enfrentam uma longa estrada até a UBS mais próxima; outros vivem a poucos quilômetros. Este projeto quantifica essa distância.

## O que eu fiz

Construí um pipeline reprodutível que:

1. Baixou os 399 polígonos municipais paranaenses e a população rural do Censo 2022 (IBGE SIDRA tabela 9923).
2. Baixou todos os estabelecimentos de atenção básica no CNES (`codigo_tipo_unidade ∈ {1, 2, 32, 40}`: postos, UBS, unidades móveis) via a API de dados abertos do Ministério da Saúde. São 3.075 estabelecimentos com coordenadas válidas.
3. Baixou todas as escolas ativas rurais e diferenciadas do INEP Censo Escolar 2024 (`TP_LOCALIZACAO == 2` OR `TP_LOCALIZACAO_DIFERENCIADA > 0`): 1.187 escolas no estado.
4. Carregou 414 unidades de extensão do IDR-Paraná georreferenciadas a partir do shapefile oficial de unidades do IDR (`Unidades_IDR_UTM`), filtrado apenas para extensão: 392 Unidades Municipais de Extensão (uma por município atendido) mais 22 Unidades Regionais de Extensão. As unidades de pesquisa (Estação/Polo de Pesquisa) e as 2 Sedes administrativas ficam de fora. Coordenadas reais, capacidade 1 por unidade.
5. Calculou um **Enhanced 2-Step Floating Catchment Area** (Luo & Qi, 2009) por serviço, com decaimento gaussiano da distância (β = 30 km) e cutoff de captação em 50 km.
6. Converteu cada escore por serviço em ranking percentil e tirou a média com pesos iguais para o índice composto.
7. Rankeou os 364 municípios com população rural relevante em quintis; marca-se o quintil inferior como "subatendido".

Tudo em Python. Todo dataset bruto vai para cache em disco. O pipeline inteiro roda em cerca de 20 minutos num laptop.

## Achados principais

- **Quintil inferior (Q1):** 73 municípios. Os 10 mais mal servidos (percentil composto, em ordem crescente) são Tibagi, Pato Bragado, Santa Helena, Capanema, Serranópolis do Iguaçu, Entre Rios do Oeste, Nova Cantu, Pérola d'Oeste, Rio Negro e Barracão. O padrão espacial junta Tibagi (interior dos Campos Gerais) a um forte grupo da Costa Oeste e do Sudoeste ao longo do reservatório de Itaipu e da fronteira com o Paraguai e a Argentina.
- **Impacto populacional:** 338.499 residentes rurais, cerca de 1 em cada 4 da população rural ranqueada do estado (27,0% de 1.253.122), vivem num município do Q1.
- **Gap de acesso:** no quintil mais mal servido, o acesso bruto per capita (E2SFCA, ponderado por população) fica cerca de 3,3x abaixo do melhor quintil para atenção primária, cerca de 1,2x para escola rural e cerca de 2,9x para extensão rural. Com a camada oficial de unidades do IDR, a extensão passa a ser a base de oferta mais granular da análise, com um gradiente espacial real e defensável.
- **Robustez:** a sobreposição do Q1 em relação aos pesos iguais é razoavelmente estável quando os pesos pendem para saúde ou extensão (91,8% no esquema pró-saúde 0,5/0,25/0,25; 79,5% no pró-extensão 0,25/0,25/0,5), mas cai bastante quando se reforça a educação (56,2% no esquema 0,25/0,5/0,25) ou sob uma ponderação derivada de PC1 (45,2%). As correlações por serviço explicam isso: o acesso à atenção primária e o acesso à extensão co-variam (r = +0,74) e se concentram nos mesmos municípios mais desenvolvidos, sobretudo o norte e o cinturão agrícola modernizado; o acesso à escola rural é a imagem espelhada (saúde vs educação r = -0,46; educação vs extensão r = -0,73), mais forte no centro-sul. Ou seja, o quinto mais mal servido do composto é onde saúde e extensão são escassas ao mesmo tempo, e esses lugares tendem a ter relativamente mais escolas rurais. O primeiro componente principal (pesos de saúde, educação e extensão = +0,88, -0,87, +0,99) é um contraste de (saúde + extensão) contra educação, não um eixo comum de acesso. A robustez é moderada; reporto os mapas por serviço ao lado do composto exatamente por isso, para que o contraste educação-versus-resto fique visível diretamente.

## Por que essa formulação

Eu poderia ter contado UBS por 5.000 residentes rurais e parado por aí. Seria enganoso. A métrica ingênua "instalações per capita" ignora que uma UBS 3 km fora do limite municipal ainda atende aquela população, e trata as divisas municipais como impermeáveis. O E2SFCA captura os dois efeitos e é o padrão atual na literatura brasileira de geografia da saúde. A justificativa metodológica completa, referências e checagens de robustez estão em `docs/METHODOLOGY.md`.

Pesos iguais entre os três serviços refletem o enquadramento constitucional (Art. 196 saúde; Art. 205 educação; Lei 12.188/2010 PNATER extensão). Reporto a sensibilidade ao peso como checagem de robustez em vez de fingir que uma ponderação específica é objetivamente correta.

## Limitações que quero corrigir numa v2

- **Distâncias em linha reta** ignoram o relevo (Serra do Mar, Serra Geral). Uma v2 com isócronas na malha viária OSM (osmnx com PBFs pré-recortados por município) apertaria o escore de saúde no Litoral Norte e Vale do Ribeira em especial.
- **Efeitos de borda** puxam para baixo os pequenos municípios da Costa Oeste no reservatório de Itaipu: a captação de 50 km é cortada pela água e pela fronteira internacional, e estabelecimentos paraguaios do outro lado não contam. É geografia real, mas uma captação nacional com borda suavizaria o efeito.
- **Capacidade CNES = 1 unidade por estabelecimento** subestima UBS mais movimentadas com várias equipes de Saúde da Família. Juntar as tabelas `EQ` do CNES resolve.
- **Escolas do INEP ancoradas no centroide municipal.** O microdado do Censo Escolar 2024 não publica mais coordenadas das escolas, então cada escola é posicionada no centroide do seu município. Isso combina com a resolução municipal da análise, mas perde o detalhe intramunicipal; uma v2 juntaria o "Catálogo de Escolas" do INEP para pontos reais.
- **Instalações fora do estado** são ignoradas. Municípios fronteiriços com SP, SC e MS teriam escores um pouco melhores com uma captação em escala nacional.

## O que essa peça mostra

O mapa é a superfície. Embaixo está um pipeline geoespacial reprodutível que ingere três bases federais, aplica uma fórmula de acessibilidade revisada por pares, normaliza para um resumo compartilhável e produz tanto um choropleth estático em qualidade de portfolio quanto um mapa interativo em Folium. Todo parâmetro está em `src/config.py`. Toda fonte tem versão. O `Makefile` reproduz tudo do zero em uma linha.

O repositório `parana-rural-access-equity` é um fim de semana de trabalho. O padrão (dados públicos, E2SFCA, ranking percentil, choropleth em quintis, writeup bilíngue) generaliza para qualquer região dos EUA ou da Europa. Basta trocar IBGE por TIGER/Line + ACS, CNES por registros estaduais de saúde, INEP por diretórios estaduais de educação. O pipeline é o pedaço de portfolio.

**Repositório:** `github.com/avnergomes/parana-rural-access-equity`
**Mapa interativo:** `avnergomes.github.io/parana-rural-access-equity/`
**Metodologia + referências:** [`docs/METHODOLOGY.md`](METHODOLOGY.md)
**Contato:** Avner Paes Gomes · avnerpaesgomes@gmail.com · [LinkedIn](https://linkedin.com/in/avnergomes)
