# faostat

A reproducible copy of the FAOSTAT bulk downloads: the food and agriculture
statistics of the Food and Agriculture Organization of the United Nations
(FAO), by country and year, for every FAOSTAT domain (production, trade, food
balances, prices, land use, inputs, emissions, forestry, population and
employment, investment, food security, SDG indicators and others).

## Source

- FAOSTAT: <https://www.fao.org/faostat/en/>
- Bulk-download catalogue: <https://bulks-faostat.fao.org/production/datasets_E.json>

The catalogue lists one zip per domain, each holding the domain's data as a
long ("Normalized") CSV for all areas, plus its code lists (areas, items,
elements, flags). Every zip it lists is taken, with the catalogue itself. The
two all-domain zips (`FAOSTAT_A-S_E.zip`, `FAOSTAT_T-Z_E.zip`), which repeat
the domain zips, the wide and per-region variants, and the FAOSTAT web API are
not used.

FAO overwrites the catalogue and the zips in place under the same names, so
the version of a copy is the UTC date it was fetched.

## Licence

Unless their metadata say otherwise, FAO statistical databases are licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.en)
complemented by the
[FAO Statistical Database Terms of Use](https://www.fao.org/contact-us/terms/db-terms-of-use/en/),
which add terms of their own (no use in promoting a commercial enterprise or
suggesting FAO endorsement, third-party data may carry other conditions,
disputes go to UNCITRAL arbitration) and require this citation format:

> FAO. [year of last update]. [Name of database: Name of dataset]. [Accessed on DD Month YYYY]. [URL] Licence: CC-BY-4.0.

FAO's
[Open Data Licensing for Statistical Databases Policy](https://openknowledge.fao.org/handle/20.500.14283/cd7464en)
says databases published before 30 November 2019 are not under a Creative
Commons licence unless marked so. Three domains in the catalogue have a
`DateUpdate` before that date (PA, HS and FA, all discontinued series) and may
not be CC BY; `MANIFEST.json` marks them with `predates_cc_by_2019_11_30`.

## Running

```sh
uv run python scripts/01_download.py    # fetch into data/raw/<YYYY-MM-DD>/
uv run python scripts/02_verify.py      # re-hash, test zips, count CSV rows
uv run python -m pytest
```

`01_download.py` waits at least a second between requests, accepts a file only
if it has the Content-Length the server states, and does not fetch again a file
already in the manifest whose sha256 still matches. `--version YYYY-MM-DD`
resumes or re-checks a copy made on another day.

## Layout

```
scripts/01_download.py       fetch the catalogue and every domain zip it lists
scripts/02_verify.py         check a copy against its manifest
tests/                       unit tests; tests/fixtures/ holds a trimmed catalogue
data/raw/<YYYY-MM-DD>/       not in git
  datasets_E.json            the catalogue as served
  *_E_All_Data_(Normalized).zip
  MANIFEST.json              per file: url, bytes, sha256, last_modified,
                             fetched_at; per domain zip also the catalogue's
                             DatasetCode, DatasetName, DateUpdate, FileSize and
                             FileRows, whether the size agrees with FileSize,
                             the Last-Modified date, and predates_cc_by_2019_11_30
```
