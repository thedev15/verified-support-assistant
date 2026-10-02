import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "photo_map"


def memory_records() -> list[tuple[str, list[str]]]:
    source = (APP / "app.js").read_text()
    records = []
    for memory_id, tags in re.findall(
        r'\{ id: "([^"]+)".*?tags: \[([^\]]+)\]', source
    ):
        records.append((memory_id, re.findall(r'"([^"]+)"', tags)))
    return records


def test_photo_map_has_fourteen_unique_memories() -> None:
    records = memory_records()
    assert len(records) == 14
    assert len({memory_id for memory_id, _ in records}) == 14


def test_filter_counts_match_the_ui_contract() -> None:
    records = memory_records()
    counts = {
        category: sum(category in tags for _, tags in records)
        for category in ("viajes", "sabores", "celebraciones")
    }
    assert counts == {"viajes": 7, "sabores": 6, "celebraciones": 5}


def test_app_is_self_contained_and_accessible() -> None:
    html = (APP / "index.html").read_text()
    css = (APP / "styles.css").read_text()
    assert 'lang="es"' in html
    assert 'aria-label="Mapa de recuerdos"' in html
    assert "https://" not in html
    assert "@import" not in css
    assert (APP / "app.js").is_file()