import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "datasets_E.trimmed.json"

_spec = importlib.util.spec_from_file_location("download", ROOT / "scripts" / "01_download.py")
download = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(download)


def test_parse_catalogue_lists_every_domain():
    domains = download.parse_catalogue(FIXTURE.read_bytes())
    assert [d["code"] for d in domains] == ["MDDW", "PA", "QCL"]
    qcl = domains[2]
    assert qcl["name"] == "Production: Crops and livestock products"
    assert qcl["url"] == (
        "https://bulks-faostat.fao.org/production/"
        "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
    )
    assert qcl["filename"] == "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
    assert qcl["date_update"] == "2025-12-31"
    assert qcl["file_size_kb"] == 33127
    assert qcl["file_rows"] == 4209110


def test_parse_catalogue_tolerates_null_fields():
    # PA has "Topic": null in the real catalogue
    pa = download.parse_catalogue(FIXTURE.read_bytes())[1]
    assert pa["code"] == "PA"
    assert pa["date_update"] == "1991-12-31"


def test_parse_catalogue_refuses_the_all_domain_zips():
    data = json.loads(FIXTURE.read_text())
    entry = dict(data["Datasets"]["Dataset"][0])
    entry["DatasetCode"] = "ALL"
    entry["FileLocation"] = "https://bulks-faostat.fao.org/production/FAOSTAT_A-S_E.zip"
    data["Datasets"]["Dataset"].append(entry)
    codes = [d["code"] for d in download.parse_catalogue(json.dumps(data).encode())]
    assert "ALL" not in codes


def test_parse_catalogue_refuses_another_host():
    data = json.loads(FIXTURE.read_text())
    data["Datasets"]["Dataset"][0]["FileLocation"] = "https://example.org/x.zip"
    with pytest.raises(ValueError):
        download.parse_catalogue(json.dumps(data).encode())


def test_parse_kb():
    assert download.parse_kb("33127KB") == 33127
    assert download.parse_kb("12KB") == 12
    with pytest.raises(ValueError):
        download.parse_kb("12MB")


def test_size_matches_catalogue():
    # QCL: 33,921,825 bytes is 33126.8 KiB, stated as 33127KB
    assert download.size_matches(33_921_825, 33127)
    assert not download.size_matches(33_921_825, 33000)


def test_version_is_the_utc_fetch_date():
    assert download.version_for(datetime(2026, 10, 5, 23, 59, tzinfo=UTC)) == "2026-10-05"


def test_predates_cc_by():
    assert download.predates_cc_by("1991-12-31")
    assert download.predates_cc_by("2019-11-29")
    assert not download.predates_cc_by("2019-11-30")
    assert not download.predates_cc_by("2025-12-31")


def test_last_modified_date():
    assert download.last_modified_date("Fri, 02 Oct 2026 08:16:55 GMT") == "2026-10-02"
    assert download.last_modified_date("") == ""
