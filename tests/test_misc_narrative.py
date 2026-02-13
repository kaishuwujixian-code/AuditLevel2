from reporting.narratives.misc import _render_misc_items


def test_misc_items_render_underlined_label_then_body() -> None:
    text = _render_misc_items(
        [
            {
                "title": "Booster pump",
                "text": "The booster pump was operating normally.",
            }
        ]
    )

    assert "<u>Booster pump:</u>" in text
    assert "<u>Booster pump:</u>\n\nThe booster pump was operating normally." == text


def test_misc_title_only_is_underlined() -> None:
    text = _render_misc_items([{"title": "Lighting", "text": ""}])
    assert text == "<u>Lighting:</u>"
