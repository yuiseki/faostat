import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("publish", ROOT / "src" / "publish.py")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)


def _tree(tmp_path, card="license: cc-by-4.0\nraw/2026-01-01/\nOld_E.zip", tamper=False):
    d = tmp_path / "data"
    run = d / "raw" / "2026-01-01"
    run.mkdir(parents=True)
    manifest = {}
    for name, flagged in (("A_E.zip", False), ("Old_E.zip", True)):
        (run / name).write_bytes(name.encode())
        e = {"sha256": hashlib.sha256(name.encode()).hexdigest(), "bytes": len(name)}
        if flagged:
            e["predates_cc_by_2019_11_30"] = True
        manifest[name] = e
    (run / "MANIFEST.json").write_text(json.dumps(manifest))
    if tamper:
        (run / "A_E.zip").write_bytes(b"x")
    for f in ("LICENSE", "provenance.yaml"):
        (d / f).write_text("x")
    (d / "README.md").write_text(card)
    return d


def test_predating_domains_are_left_out_and_the_rest_listed(tmp_path):
    files, left = p.collect(_tree(tmp_path))
    assert left == ["Old_E.zip"]
    assert "raw/2026-01-01/A_E.zip" in files and "raw/2026-01-01/Old_E.zip" not in files


def test_the_card_must_say_which_domain_is_left_out(tmp_path):
    with pytest.raises(SystemExit, match="left out"):
        p.collect(_tree(tmp_path, card="license: cc-by-4.0\nraw/2026-01-01/"))


def test_a_changed_zip_stops_the_push(tmp_path):
    with pytest.raises(SystemExit, match="not the file in its manifest"):
        p.collect(_tree(tmp_path, tamper=True))


def test_a_card_without_licence_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="license"):
        p.collect(_tree(tmp_path, card="raw/2026-01-01/ Old_E.zip"))
