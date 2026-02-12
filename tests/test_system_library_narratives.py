from reporting.narratives import cooling, dhw, heating, ventilation


def _project(key):
    return {
        "answers": {
            key: [
                {"title": "Preset Title", "text": "Preset paragraph."},
            ]
        }
    }


def test_heating_library_items_rendered():
    text = heating.render_block(_project("heating_items"))
    assert "Preset paragraph." in text


def test_cooling_library_items_rendered():
    text = cooling.render_block(_project("cooling_items"))
    assert "Preset paragraph." in text


def test_dhw_library_items_rendered():
    text = dhw.render_block(_project("dhw_items"))
    assert "Preset paragraph." in text


def test_ventilation_library_items_rendered():
    text = ventilation.render_block(_project("ventilation_items"))
    assert "Preset paragraph." in text
