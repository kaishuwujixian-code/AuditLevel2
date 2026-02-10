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

    assert "B̲o̲o̲s̲t̲e̲r̲ p̲u̲m̲p̲:̲" in text
    assert "B̲o̲o̲s̲t̲e̲r̲ p̲u̲m̲p̲:̲\n\nThe booster pump was operating normally." == text


def test_misc_title_only_is_underlined() -> None:
    text = _render_misc_items([{"title": "Lighting", "text": ""}])
    assert text == "L̲i̲g̲h̲t̲i̲n̲g̲:̲"
