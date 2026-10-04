#!/usr/bin/env python3
"""Check every fetched version against its MANIFEST.json.

For each data/raw/<version>/:
  - every file in the manifest exists and has its sha256
  - the catalogue parses and lists exactly the domain zips in the manifest
  - every zip passes zipfile.testzip
  - every CSV inside every zip is read to the end with the csv module and its
    rows (header excluded) are counted

ok/FAIL lines are printed; the exit status is non-zero on any FAIL. Where the
row count of a domain's data CSV differs from the catalogue's FileRows, or its
size from FileSize, a "note" line is printed: the catalogue describes FAO's
data, not this copy, and the two are not always updated together.

    uv run python scripts/02_verify.py
"""

import csv
import hashlib
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

csv.field_size_limit(1 << 30)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def count_rows(zpath: Path) -> dict[str, int]:
    """Rows (header excluded) of every CSV in the zip, read with the csv module.

    Bytes that are not UTF-8 are replaced, which cannot change a row count.
    """
    counts = {}
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with z.open(name) as f:
                text = io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline="")
                counts[name] = max(sum(1 for _ in csv.reader(text)) - 1, 0)
    return counts


def data_member(zip_name: str, names: list[str]) -> str | None:
    """The data CSV of a domain zip is the zip's own name with .csv."""
    want = zip_name[: -len(".zip")] + ".csv"
    return want if want in names else None


def load_download():
    spec = importlib.util.spec_from_file_location("download", ROOT / "scripts" / "01_download.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    download = load_download()
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what)
        if not ok:
            failures.append(what)

    versions = (
        sorted(p for p in RAW.iterdir() if (p / "MANIFEST.json").exists()) if RAW.exists() else []
    )
    check(bool(versions), f"{len(versions)} version(s) under data/raw")
    for d in versions:
        v = d.name
        manifest = json.loads((d / "MANIFEST.json").read_text())
        for name, m in manifest.items():
            p = d / name
            check(p.exists() and sha256(p) == m["sha256"], f"{v}/{name}: sha256")

        domains = download.parse_catalogue((d / download.CATALOGUE_NAME).read_bytes())
        listed = {x["filename"] for x in domains}
        have = {n for n in manifest if n.endswith(".zip")}
        check(listed == have, f"{v}: {len(have)} zips, the {len(listed)} the catalogue lists")

        for x in domains:
            name = x["filename"]
            p = d / name
            if not p.exists():
                continue
            with zipfile.ZipFile(p) as z:
                bad = z.testzip()
                names = z.namelist()
            check(bad is None, f"{v}/{name}: testzip")
            counts = count_rows(p)
            member = data_member(name, names)
            check(member is not None, f"{v}/{x['code']}: data CSV present")
            total = sum(counts.values())
            print(f"ok    {v}/{x['code']}: {len(counts)} CSVs, {total:,} rows read")
            if member and counts[member] != x["file_rows"]:
                print(
                    f"note  {v}/{x['code']}: {counts[member]:,} rows, catalogue FileRows {x['file_rows']:,}"
                )
            if not manifest[name].get("size_matches_catalogue", True):
                print(
                    f"note  {v}/{x['code']}: {manifest[name]['bytes']:,} bytes, catalogue FileSize {x['file_size_kb']}KB"
                )

    if failures:
        print(f"\n{len(failures)} checks failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
