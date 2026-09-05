import re
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_questdb_import_is_contained_inside_hot_store_adapter() -> None:
    imports = []
    for source in (ROOT / "src" / "live15_quant_v2").rglob("*.py"):
        if re.search(r"^import questdb$", source.read_text(encoding="utf-8"), re.MULTILINE):
            imports.append(source.relative_to(ROOT).as_posix())

    assert imports == [
        "src/live15_quant_v2/data/storage/hot_store/questdb_adapter.py",
    ]
