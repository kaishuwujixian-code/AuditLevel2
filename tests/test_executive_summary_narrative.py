from reporting.narratives.executive_summary import render_block


def test_render_block_uses_library_items() -> None:
    project = {
        "answers": {
            "executive_summary_items": [
                {
                    "title": "central boiler plant performance",
                    "text": "Space heating is provided by {number} boilers.",
                }
            ]
        }
    }
    rendered = render_block(project)
    assert "central boiler plant performance" in rendered
    assert "Space heating is provided" in rendered


def test_render_block_appends_override_text() -> None:
    project = {
        "answers": {
            "executive_summary_items": [
                {"title": "one", "text": "first"},
            ],
            "executive_summary_block_override": "manual override",
        }
    }
    rendered = render_block(project)
    assert "first" in rendered
    assert rendered.endswith("manual override")
