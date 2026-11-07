"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import afs_constants as C
import afs_evaluation as ev
import afs_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert (preset["limit"] - C.LIMIT_MIN) % C.LIMIT_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["family"], first["m"], first["depot"], first["Q"], first["limit"], first["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_constants_are_consistent():
    assert C.M_MIN <= C.DEFAULT_M <= C.M_MAX <= C.EXACT_LIVE_MAX <= C.ENUM_MAX <= max(C.BAND_METHOD_SIZES) and C.Q_MIN >= C.LOAD_MAX and C.Q_MIN <= C.DEFAULT_Q <= C.Q_MAX
    assert C.LIMIT_MIN <= C.DEFAULT_LIMIT <= C.LIMIT_MAX and (C.DEFAULT_LIMIT - C.LIMIT_MIN) % C.LIMIT_STEP == 0 and C.BAND_Q >= C.LOAD_MAX
    assert set(C.BAND_ENUM_SIZES) <= set(range(C.M_MIN, C.ENUM_MAX + 1)) and C.LIVE_K_INSERT[0] <= C.LIVE_K_INSERT[2] <= C.LIVE_K_INSERT[1] and C.LIVE_K_ORDERS[0] <= C.LIVE_K_ORDERS[2] <= C.LIVE_K_ORDERS[1]
    assert C.HAND_Q >= max(C.HAND_LOAD) and len(C.HAND_POINTS) == 1 + 2 * len(C.HAND_LOAD) and C.KS_INSERT == 10 and C.KS_ORDERS == 100
