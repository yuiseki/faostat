---
license: cc-by-4.0
license_name: cc-by-4.0
license_link: https://creativecommons.org/licenses/by/4.0/legalcode.en
language:
- en
task_categories:
- tabular-regression
- time-series-forecasting
tags:
- fao
- faostat
- agriculture
- food-security
- trade
- emissions
- land-use
- forestry
size_categories:
- 100M<n<1B
---

# faostat

The FAOSTAT bulk downloads of the Food and Agriculture Organization of the United Nations
(FAO): 66 domain zips, as the bulk-download catalogue listed them on
2026-10-04 (production, trade, food balances, prices, land use, inputs, emissions,
forestry, population and employment, investment, food security, SDG indicators and others).
Each zip holds the domain's data as a long ("Normalized") CSV for all areas, plus its code
lists (areas, items, elements, flags). The zips are exactly as FAO serves them; this
dataset is a mirror, not a reformatting.

Source: <https://www.fao.org/faostat/en/>; catalogue https://bulks-faostat.fao.org/production/datasets_E.json
(Last-Modified Fri, 02 Oct 2026 08:16:55 GMT).

## The data follows upstream corrections

FAO overwrites the catalogue and the zips in place under the same names. This dataset
therefore holds one run, the newest, and is replaced as a whole when it is fetched again;
older runs are not kept here. The current run is `raw/2026-10-04/`; `MANIFEST.json` gives
for each file its URL, size, sha256, Last-Modified, fetch time and the catalogue's own
entry (domain code, name, `DateUpdate`, row count).

## Layout

```
raw/2026-10-04/MANIFEST.json
raw/2026-10-04/datasets_E.json                    the catalogue, as received
raw/2026-10-04/<Domain>_E_All_Data_(Normalized).zip   66 files, 1.52 GB
```

The CSVs in each zip are as FAO writes them. Most are valid UTF-8; some are not (8 data
files and 7 code lists on 2026-10-04), so open them with an explicit legacy encoding such as
Latin-1 when UTF-8 fails. Columns are, for most domains,
`Area Code`, `Area Code (M49)`, `Area`, `Item Code`, `Item`, `Element Code`, `Element`,
`Year Code`, `Year`, `Unit`, `Value`, `Flag`, `Note`.

## Left out: domains that may not be under CC BY

FAO's licensing policy (https://openknowledge.fao.org/handle/20.500.14283/cd7464en) puts its statistical databases under CC BY 4.0 from
30 November 2019 on, and says databases published before that date are not under a
Creative Commons licence unless marked so. Three discontinued series have a catalogue
`DateUpdate` before that date, and nothing in the catalogue marks them. They are not
published here (`MANIFEST.json` still lists them, with the reason):

- `Food_Aid_Shipments_WFP_E_All_Data_(Normalized).zip` (FA, Discontinued archives and data series: Food Aid Shipments (WFP); last update 2016-12-22, 31,114 rows)
- `Indicators_from_Household_Surveys_E_All_Data_(Normalized).zip` (HS, Discontinued archives and data series: Indicators from Household Surveys (gender, area, socioeconomics); last update 2014-07-31, 148,620 rows)
- `PricesArchive_E_All_Data_(Normalized).zip` (PA, Discontinued archives and data series: Producer Prices (old series); last update 1991-12-31, 139,713 rows)

## Licence

FAO statistical databases are licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/legalcode.en), complemented by the FAO
Statistical Database Terms of Use (https://www.fao.org/contact-us/terms/db-terms-of-use/en/), which add terms of their own: no use in
promoting a commercial enterprise or suggesting FAO endorsement, data of third parties
may carry other conditions, and disputes go to UNCITRAL arbitration. Required citation
format:

> FAO. [year of last update]. [Name of database: Name of dataset]. [Accessed on DD Month YYYY]. [URL] Licence: CC-BY-4.0.

Collection code: <https://github.com/yuiseki/faostat> (MIT).
