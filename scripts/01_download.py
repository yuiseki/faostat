#!/usr/bin/env python3
"""Fetch the FAOSTAT bulk-download catalogue and every domain zip it lists.

The catalogue is https://bulks-faostat.fao.org/production/datasets_E.json.
Each of its entries (one per domain) names a zip in FileLocation; that zip is
taken as served. The two all-domain zips (FAOSTAT_A-S_E.zip and
FAOSTAT_T-Z_E.zip) are not listed in the catalogue, duplicate the domain zips,
and are refused if they ever appear in it. Nothing else on the site is called.

FAO overwrites the catalogue and the zips in place under the same names, so the
version is the UTC date of the fetch: everything goes under
data/raw/<YYYY-MM-DD>/. data/raw/<version>/MANIFEST.json records, for each
file, its URL, size, sha256, Last-Modified and fetch time, and for each domain
what the catalogue states about it (code, name, DateUpdate, FileSize,
FileRows), whether the size agrees with FileSize, and whether DateUpdate is
before 2019-11-30, the date from which FAO applies CC BY to its statistical
databases.

A file is accepted only if it has the Content-Length the server states. A file
already in the manifest whose sha256 still matches is not fetched again; the
catalogue already saved under today's version is reused rather than refetched.

    uv run python scripts/01_download.py [--version YYYY-MM-DD]
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CATALOGUE_URL = "https://bulks-faostat.fao.org/production/datasets_E.json"
CATALOGUE_NAME = "datasets_E.json"
HOST_PREFIX = "https://bulks-faostat.fao.org/production/"
ALL_DOMAIN_ZIPS = {"FAOSTAT_A-S_E.zip", "FAOSTAT_T-Z_E.zip"}
CC_BY_FROM = date(2019, 11, 30)
UA = "faostat/1 (+https://github.com/yuiseki/faostat)"
PAUSE = 1.0


def parse_kb(s: str) -> int:
    if not s.endswith("KB"):
        raise ValueError(f"FileSize not in KB: {s!r}")
    return int(s[:-2])


def parse_catalogue(data: bytes) -> list[dict]:
    """Return one dict per domain zip listed in datasets_E.json."""
    out = []
    for e in json.loads(data)["Datasets"]["Dataset"]:
        url = e["FileLocation"]
        if not url.startswith(HOST_PREFIX):
            raise ValueError(f"{e['DatasetCode']}: unexpected location {url}")
        filename = urllib.parse.unquote(url.rsplit("/", 1)[1])
        if filename in ALL_DOMAIN_ZIPS:
            continue
        out.append(
            {
                "code": e["DatasetCode"],
                "name": e["DatasetName"],
                "url": url,
                "filename": filename,
                "date_update": e["DateUpdate"][:10],
                "file_size_kb": parse_kb(e["FileSize"]),
                "file_rows": int(e["FileRows"]),
            }
        )
    return out


def size_matches(nbytes: int, kb: int) -> bool:
    """The catalogue's FileSize is KiB; true if the file is within 1 KiB of it."""
    return abs(nbytes / 1024 - kb) < 1


def version_for(now: datetime) -> str:
    return now.astimezone(UTC).strftime("%Y-%m-%d")


def predates_cc_by(date_update: str) -> bool:
    return date.fromisoformat(date_update) < CC_BY_FROM


def last_modified_date(header: str) -> str:
    if not header:
        return ""
    return parsedate_to_datetime(header).astimezone(UTC).strftime("%Y-%m-%d")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


_last_request = 0.0


def fetch(url: str, dest: Path) -> dict:
    global _last_request
    wait = PAUSE - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = dest.with_name(dest.name + ".part")
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
            length = r.headers.get("Content-Length")
            lm = r.headers.get("Last-Modified", "")
    finally:
        _last_request = time.monotonic()
    got = tmp.stat().st_size
    if length is not None and got != int(length):
        tmp.unlink()
        raise SystemExit(f"{url}: got {got} bytes, the server stated {length}")
    tmp.replace(dest)
    return {
        "url": url,
        "bytes": got,
        "sha256": sha256(dest),
        "last_modified": lm,
        "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def have(d: Path, manifest: dict, name: str) -> bool:
    return name in manifest and (d / name).exists() and sha256(d / name) == manifest[name]["sha256"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=version_for(datetime.now(UTC)))
    version = ap.parse_args().version
    d = RAW / version
    d.mkdir(parents=True, exist_ok=True)
    mpath = d / "MANIFEST.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}

    def save() -> None:
        mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")

    if not have(d, manifest, CATALOGUE_NAME):
        manifest[CATALOGUE_NAME] = fetch(CATALOGUE_URL, d / CATALOGUE_NAME)
        save()
        print(f"{version}/{CATALOGUE_NAME}: {manifest[CATALOGUE_NAME]['last_modified']}")
    domains = parse_catalogue((d / CATALOGUE_NAME).read_bytes())
    stated = sum(x["file_size_kb"] for x in domains) * 1024
    print(f"{len(domains)} domains in the catalogue, {stated:,} bytes stated")

    fetched = 0
    for x in domains:
        name = x["filename"]
        if have(d, manifest, name):
            continue
        m = fetch(x["url"], d / name)
        m["catalogue"] = {
            "DatasetCode": x["code"],
            "DatasetName": x["name"],
            "DateUpdate": x["date_update"],
            "FileSize_KB": x["file_size_kb"],
            "FileRows": x["file_rows"],
        }
        m["size_matches_catalogue"] = size_matches(m["bytes"], x["file_size_kb"])
        m["last_modified_date"] = last_modified_date(m["last_modified"])
        m["predates_cc_by_2019_11_30"] = predates_cc_by(x["date_update"])
        manifest[name] = m
        save()
        fetched += 1
        flag = "" if m["size_matches_catalogue"] else f"  SIZE differs from {x['file_size_kb']}KB"
        print(
            f"{x['code']}: {m['bytes']:,} bytes, DateUpdate {x['date_update']}, "
            f"Last-Modified {m['last_modified_date']}{flag}"
        )
    save()
    print(f"fetched {fetched} domain zips; {len(domains) - fetched} already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
