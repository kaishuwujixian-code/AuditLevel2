import json

from core.library_catalog import (
    load_library_catalog,
    save_library_catalog_data,
    validate_library_catalog_data,
)


def test_validate_library_catalog_data_accepts_valid_data():
    validate_library_catalog_data(
        {
            "categories": [{"code": "system", "title": "System"}],
            "items": [
                {
                    "id": "ahu",
                    "title": "Central AHU",
                    "category": "system",
                    "text": "Sample text",
                }
            ],
        }
    )


def test_validate_library_catalog_data_rejects_unknown_category():
    try:
        validate_library_catalog_data(
            {
                "categories": [{"code": "system", "title": "System"}],
                "items": [{"id": "ahu", "category": "other", "title": "X", "text": "Y"}],
            }
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown category" in str(exc)


def test_save_and_load_library_catalog_data_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalogs_dir = tmp_path / "catalogs"
    catalogs_dir.mkdir()
    catalog_path = catalogs_dir / "heating_catalog.json"
    catalog_path.write_text(json.dumps({"categories": [], "items": []}), encoding="utf-8")

    import core.library_catalog as library_catalog

    monkeypatch.setattr(library_catalog, "CATALOGS_DIR", str(catalogs_dir))
    save_library_catalog_data(
        "heating_catalog.json",
        {
            "categories": [{"code": "equipment_condition", "title": "Equipment condition"}],
            "items": [
                {
                    "id": "sample_item",
                    "title": "Sample",
                    "category": "equipment_condition",
                    "text": "Sample text",
                }
            ],
        },
        backup=False,
    )

    catalog = load_library_catalog("heating_catalog.json")
    assert catalog.categories[0]["code"] == "equipment_condition"
    assert catalog.items["sample_item"]["category"] == "equipment_condition"
