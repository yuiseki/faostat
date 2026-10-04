import importlib.util
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("verify", ROOT / "scripts" / "02_verify.py")
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)


def make_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "X_E_All_Data_(Normalized).csv",
            'Area Code,Area,Value\n"2","Afghanistan","1.0"\n"3","Albania, Rep.","2.0"\n'
            '"4","Line\nbreak","3.0"\n',
        )
        z.writestr("X_E_Flags.csv", "Flag,Description\nA,Official figure\n")


def test_count_rows_excludes_the_header_and_follows_quoted_newlines(tmp_path):
    p = tmp_path / "X_E_All_Data_(Normalized).zip"
    make_zip(p)
    counts = verify.count_rows(p)
    assert counts == {"X_E_All_Data_(Normalized).csv": 3, "X_E_Flags.csv": 1}


def test_data_member_is_the_one_named_like_the_zip():
    names = ["X_E_All_Data_(Normalized).csv", "X_E_Flags.csv"]
    assert verify.data_member("X_E_All_Data_(Normalized).zip", names) == names[0]
    assert verify.data_member("Y.zip", names) is None


def test_count_rows_reads_latin1_without_failing(tmp_path):
    p = tmp_path / "a.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("a.csv", io.BytesIO("h\nC\xf4te\n".encode("latin-1")).getvalue())
    assert verify.count_rows(p) == {"a.csv": 1}
