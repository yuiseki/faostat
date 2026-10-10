#!/usr/bin/env python3
"""Write data/README.md (the Hub card), data/LICENSE and data/provenance.yaml.

Counts come from the manifest of the newest run under data/raw/.

    uv run python scripts/03_card.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CC = "https://creativecommons.org/licenses/by/4.0/legalcode.en"
TERMS = "https://www.fao.org/contact-us/terms/db-terms-of-use/en/"
POLICY = "https://openknowledge.fao.org/handle/20.500.14283/cd7464en"
CATALOGUE = "https://bulks-faostat.fao.org/production/datasets_E.json"


def run_facts() -> dict:
    d = sorted((DATA / "raw").glob("*/MANIFEST.json"))[-1].parent
    m = json.loads((d / "MANIFEST.json").read_text())
    zips = {k: v for k, v in m.items() if isinstance(v, dict) and k.endswith(".zip")}
    out = {k: v for k, v in zips.items() if v.get("predates_cc_by_2019_11_30")}
    kept = {k: v for k, v in zips.items() if k not in out}
    return {
        "run": d.name,
        "kept": kept,
        "out": out,
        "bytes": sum(v["bytes"] for v in kept.values()),
        "catalogue": m["datasets_E.json"],
    }


def card(f: dict) -> str:
    out = "\n".join(
        f"- `{k}` ({v['catalogue']['DatasetCode']}, {v['catalogue']['DatasetName']}; "
        f"last update {v['catalogue']['DateUpdate']}, {v['catalogue']['FileRows']:,} rows)"
        for k, v in f["out"].items()
    )
    return f"""---
license: cc-by-4.0
license_name: cc-by-4.0
license_link: {CC}
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
- 10M<n<100M
---

# faostat

The FAOSTAT bulk downloads of the Food and Agriculture Organization of the United Nations
(FAO): {len(f["kept"])} domain zips, as the bulk-download catalogue listed them on
{f["run"]} (production, trade, food balances, prices, land use, inputs, emissions,
forestry, population and employment, investment, food security, SDG indicators and others).
Each zip holds the domain's data as a long ("Normalized") CSV for all areas, plus its code
lists (areas, items, elements, flags). The zips are exactly as FAO serves them; this
dataset is a mirror, not a reformatting.

Source: <https://www.fao.org/faostat/en/>; catalogue {CATALOGUE}
(Last-Modified {f["catalogue"]["last_modified"]}).

## The data follows upstream corrections

FAO overwrites the catalogue and the zips in place under the same names. This dataset
therefore holds one run, the newest, and is replaced as a whole when it is fetched again;
older runs are not kept here. The current run is `raw/{f["run"]}/`; `MANIFEST.json` gives
for each file its URL, size, sha256, Last-Modified, fetch time and the catalogue's own
entry (domain code, name, `DateUpdate`, row count).

## Layout

```
raw/{f["run"]}/MANIFEST.json
raw/{f["run"]}/datasets_E.json                    the catalogue, as received
raw/{f["run"]}/<Domain>_E_All_Data_(Normalized).zip   {len(f["kept"])} files, {f["bytes"] / 1e9:.2f} GB
```

The CSVs in each zip are as FAO writes them. Most are valid UTF-8; some are not (8 data
files and 7 code lists on 2026-10-04), so open them with an explicit legacy encoding such as
Latin-1 when UTF-8 fails. Columns are, for most domains,
`Area Code`, `Area Code (M49)`, `Area`, `Item Code`, `Item`, `Element Code`, `Element`,
`Year Code`, `Year`, `Unit`, `Value`, `Flag`, `Note`.

## Left out: domains that may not be under CC BY

FAO's licensing policy ({POLICY}) puts its statistical databases under CC BY 4.0 from
30 November 2019 on, and says databases published before that date are not under a
Creative Commons licence unless marked so. Three discontinued series have a catalogue
`DateUpdate` before that date, and nothing in the catalogue marks them. They are not
published here (they are in the collection repository's manifest):

{out}

## Licence

FAO statistical databases are licensed under CC BY 4.0 ({CC}), complemented by the FAO
Statistical Database Terms of Use ({TERMS}), which add terms of their own: no use in
promoting a commercial enterprise or suggesting FAO endorsement, data of third parties
may carry other conditions, and disputes go to UNCITRAL arbitration. Required citation
format:

> FAO. [year of last update]. [Name of database: Name of dataset]. [Accessed on DD Month YYYY]. [URL] Licence: CC-BY-4.0.

Collection code: <https://github.com/yuiseki/faostat> (MIT).
"""


def licence_file(f: dict) -> str:
    return f"""The contents of data/raw/ are FAOSTAT bulk downloads, © FAO, unchanged.

They are licensed under CC BY 4.0 ({CC}), complemented by the FAO Statistical Database
Terms of Use ({TERMS}): no use in promoting a commercial enterprise or suggesting FAO
endorsement; data of third parties may carry other conditions; disputes go to UNCITRAL
arbitration.

Citation format required by FAO:

  FAO. [year of last update]. [Name of database: Name of dataset]. [Accessed on DD Month YYYY]. [URL] Licence: CC-BY-4.0.

Databases published before 30 November 2019 are not under a Creative Commons licence unless
marked so ({POLICY}); the {len(f["out"])} domains with such a date are not included.

The code of the repository this dataset was built from is MIT licensed.
"""


def provenance(f: dict) -> str:
    out = "\n".join(f"    - {k}" for k in f["out"])
    return f"""# Where this data comes from and what was done to it.

source:
  name: FAOSTAT bulk downloads
  publisher: Food and Agriculture Organization of the United Nations (FAO)
  portal: https://www.fao.org/faostat/en/
  catalogue: {CATALOGUE}  # Last-Modified {f["catalogue"]["last_modified"]}
  versions: none. FAO overwrites in place; this dataset holds the newest run and follows upstream corrections.
  licence:
    applied: CC BY 4.0 ({CC}) and the FAO Statistical Database Terms of Use ({TERMS})
    card: "license: cc-by-4.0"
    attribution_required: true
    policy_checked: {POLICY}
    left_out_because_predating_2019_11_30:
{out}
  citation: >-
    FAO. [year of last update]. [Name of database: Name of dataset]. [Accessed on {f["run"]}].
    https://www.fao.org/faostat/en/ Licence: CC-BY-4.0.

run:
  date: {f["run"]}
  domains_published: {len(f["kept"])}
  domains_left_out: {len(f["out"])}

processing:
  - none: the zips are as served, each checked against the sha256 in MANIFEST.json
"""


def main() -> int:
    f = run_facts()
    (DATA / "README.md").write_text(card(f), encoding="utf-8")
    (DATA / "LICENSE").write_text(licence_file(f), encoding="utf-8")
    (DATA / "provenance.yaml").write_text(provenance(f), encoding="utf-8")
    print(f"{len(f['kept'])} zips, {f['bytes']:,} bytes; left out {len(f['out'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
