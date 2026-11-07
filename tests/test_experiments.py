"""Die fünf Experimente der App per AppTest: zwei Ebenen, Auftragsfolge von Hand, Seltenheit, Verfahren, Einfügepositionen; dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import afs_constants as C
import afs_evaluation as ev
import afs_model as M
from afs_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SETTING_KEYS = {"family": "family_select", "m": "m_slider", "depot": "depot_select", "Q": "cap_slider", "limit": "limit_slider", "seed": "seed_input"}


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.error])


def test_the_default_shows_the_hand_example():
    at = _app()
    text = _texts(at)
    assert "Die Dominanz gilt auf beiden Ebenen" in text
    assert any(m.value == "43,42" for m in at.metric)
    assert "Von 24 Auftragsfolgen liefern 16 (66,7 %) das Optimum 43,42" in text


def test_every_preset_runs_and_shows_its_numbers():
    for name in C.PRESETS:
        at = _app(name)
        text = _texts(at)
        assert "Die Dominanz gilt auf beiden Ebenen" in text and "Zwei Ebenen" in " ".join(s.value for s in at.subheader), name
    text = _texts(_app("Haltefolge ohne Zerlegung (6 Aufträge)"))
    assert "keine zulässige Zerlegung" in text and "lassen sich 0 (0,00 %)" in text
    assert "Von 5040 Auftragsfolgen liefern 144 (2,9 %) das Optimum 651,81" in _texts(_app("Das Optimum ist selten (7 Aufträge)"))
    assert "Einfügen mit einer Reihenfolge +20,0 %" in _texts(_app("Einfügen gegen Folge (7 Aufträge)"))


def test_seeds_and_the_order_selection_can_be_changed():
    at = _app()
    at.number_input(key="stop_seed").set_value(5).run()
    at.number_input(key="order_seed").set_value(6).run()
    assert not at.exception
    at.multiselect(key="order_sel_4_0").set_value([1, 3, 2]).run()
    assert not at.exception and "Die Folge 1 3 2 4" in _texts(at)
    at.multiselect(key="order_sel_4_0").set_value([1, 2, 3, 4]).run()
    assert "diese Folge liefert es." in _texts(at)


def test_live_sliders_and_the_method_view():
    at = _app("Einfügen gegen Folge (7 Aufträge)")
    at.slider(key="ins_k").set_value(3).run()
    at.slider(key="ord_k").set_value(20).run()
    at.number_input(key="cmp_seed").set_value(4).run()
    assert not at.exception and "bestes von 3 Reihenfolgen" in _texts(at) and "bestes von 20 Folgen" in _texts(at)
    for key in ("opt", "ins1", "insk", "nn", "rand1", "randk"):
        at.selectbox(key="show_method").set_value(key).run()
        assert not at.exception, key


def test_every_size_family_and_limit_runs():
    at = _app()
    at.selectbox(key="family_select").set_value(1).run()
    for m in range(C.M_MIN, C.M_MAX + 1):
        at.slider(key="m_slider").set_value(m).run()
        assert not at.exception, m
    at.slider(key="limit_slider").set_value(100).run()
    assert not at.exception and "Routen im Optimum" in " ".join(x.label for x in at.metric)
    at.slider(key="limit_slider").set_value(C.LIMIT_MIN).run()
    at.slider(key="cap_slider").set_value(C.Q_MIN).run()
    assert not at.exception


def test_band_selection_and_insertion_choices():
    at = _app()
    for m in C.BAND_METHOD_SIZES:
        at.radio(key="band_m").set_value(m).run()
        assert not at.exception and f"{m} Aufträgen" in _texts(at), m
    at.selectbox(key="pos_route_4_0").set_value(1).run()
    assert not at.exception
    at.selectbox(key="pos_req_4_0_1").set_value(1).run()
    assert not at.exception and "Positionspaare" in _texts(at)


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["family"], preset["m"], preset["depot"], preset["Q"], preset["limit"], preset["seed"])
        inst = ev.build_instance(s)
        data = build_pdf(s, inst, M.solve(inst))
        assert data[:5] == b"%PDF-" and len(data) > 1500
