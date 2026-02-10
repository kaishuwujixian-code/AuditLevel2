from reporting.rulesets.engine import render_ruleset_block


def _project_with_answers(**answers):
    return {"answers": answers}


def test_heating_defaults_and_central_boiler_sentence() -> None:
    project = _project_with_answers(heating_heat_source="central_hydronic_boiler_plant")
    rendered = render_ruleset_block(
        project,
        ruleset_filename="heating.rules.json",
        target_block="heating",
        block_ref="{Central Heating Systems block}",
    )
    assert (
        "The boilers, pumps, and associated piping were observed to be in fair to good condition."
        in rendered
    )
    assert (
        "The existing heating system equipment was observed to be in fair to good condition."
        in rendered
    )


def test_cooling_uses_provided_system_condition() -> None:
    project = _project_with_answers(cooling_system_condition="poor")
    rendered = render_ruleset_block(
        project,
        ruleset_filename="cooling.rules.json",
        target_block="cooling",
        block_ref="{Central Cooling Systems block}",
    )
    assert "The existing cooling system equipment was observed to be in poor condition." in rendered


def test_ventilation_default_system_condition() -> None:
    project = _project_with_answers()
    rendered = render_ruleset_block(
        project,
        ruleset_filename="ventilation.rules.json",
        target_block="ventilation",
        block_ref="{Central Ventilation System Block}",
    )
    assert (
        "The existing central ventilation equipment was observed to be in fair to good condition."
        in rendered
    )


def test_dhw_default_system_condition() -> None:
    project = _project_with_answers()
    rendered = render_ruleset_block(
        project,
        ruleset_filename="dhw.rules.json",
        target_block="dhw",
        block_ref="{DHW System Block}",
    )
    assert (
        "The existing domestic hot water equipment was observed to be in fair to good condition."
        in rendered
    )
