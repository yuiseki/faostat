#!/usr/bin/env python3
"""Push the card, the licence, the provenance and the current run's domain zips to the Hub.

FAO overwrites the catalogue and the zips in place, so the Hub holds one run only: the
newest under data/raw/. Each zip goes up unchanged after its sha256 is checked against
MANIFEST.json, and the files of older runs are deleted on the Hub in the same commit (the
data follows upstream corrections). The domains FAO's licensing policy does not clearly
put under CC BY (those marked predates_cc_by_2019_11_30) are not uploaded; they stay in
data/raw/ and in the manifest. The card must name the run and every domain left out.

    uv run python src/publish.py             # dry run: list the files and their total size
    uv run python src/publish.py --push
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/faostat"
DELETE_PATTERNS = ["raw/**"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def current_run(data: Path) -> Path:
    runs = sorted((data / "raw").glob("*/MANIFEST.json"))
    if not runs:
        raise SystemExit("no run under data/raw/; run scripts/01_download.py")
    return runs[-1].parent


def collect(data: Path) -> tuple[list[str], list[str]]:
    """(files to upload relative to data/, names left out); stops on anything the card or manifest refutes."""
    card = (data / "README.md").read_text(encoding="utf-8")
    if "license: cc-by-4.0" not in card:
        raise SystemExit("the card does not declare license: cc-by-4.0")
    d = current_run(data)
    if f"raw/{d.name}/" not in card:
        raise SystemExit(f"the card does not name the current run raw/{d.name}/")
    manifest = json.loads((d / "MANIFEST.json").read_text())
    files = ["README.md", "LICENSE", "provenance.yaml", f"raw/{d.name}/MANIFEST.json"]
    left_out = []
    for name, e in manifest.items():
        if not isinstance(e, dict) or "sha256" not in e:
            continue
        if e.get("predates_cc_by_2019_11_30"):
            if name not in card:
                raise SystemExit(f"the card does not say that {name} is left out")
            left_out.append(name)
            continue
        if sha256(d / name) != e["sha256"]:
            raise SystemExit(f"raw/{d.name}/{name} is not the file in its manifest")
        files.append(f"raw/{d.name}/{name}")
    stray = (
        {p.relative_to(data).as_posix() for p in d.iterdir() if p.is_file()}
        - set(files)
        - {f"raw/{d.name}/{n}" for n in left_out}
    )
    if stray:
        raise SystemExit(f"files in the run that the manifest does not list: {sorted(stray)[:5]}")
    return files, left_out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    files, left_out = collect(DATA)
    total = sum((DATA / f).stat().st_size for f in files)
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes ({total / 1e9:.2f} GB)")
    for n in left_out:
        print(f"  left out (licence): {n}")
    print(f"  remote files matching {DELETE_PATTERNS} and not uploaded are deleted")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        folder_path=str(DATA), repo_id=a.repo, repo_type="dataset", allow_patterns=files,
        delete_patterns=DELETE_PATTERNS,
    )  # fmt: skip
    print(f"\npushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
