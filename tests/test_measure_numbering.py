from reporting.narratives import measures


def test_render_block_numbers_selected_measures():
    project = {"answers": {"selected_measures": ["bas_upgrade", "condensing_boiler_retrofit"]}}
    text = measures.render_block(project)
    assert "Measure 1 –" in text
    assert "Measure 2 –" in text


def test_render_block_numbers_structured_measures():
    project = {
        "answers": {
            "measures": [
                {"measure_title": "First", "existing_conditions": "A"},
                {"measure_title": "Second", "retrofit_conditions": "B"},
            ]
        }
    }
    text = measures.render_block(project)
    assert "Measure 1 – First" in text
    assert "Measure 2 – Second" in text
