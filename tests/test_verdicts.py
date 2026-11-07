"""Verdikte sind reine Funktionen: jede Zahl im Text stammt aus der Rechnung, Art und Wortlaut folgen den Schwellen."""

import pytest

import afs_constants as C
import afs_evaluation as ev
import afs_model as M


def _inst(**kw):
    s = ev.Settings(**kw)
    return s, ev.build_instance(s)


def test_levels_verdict_without_a_stop_split():
    s, inst = _inst(family=1, m=6, depot=0, Q=6, limit=50, seed=3)
    lv = ev.levels(inst, 1, 1, 200)
    assert lv.stop_blocks is None and lv.sample_feasible == 0
    kind, text = ev.verdict_levels(inst, lv)
    opt = M.solve(inst).cost
    assert kind == "warning" and "keine zulässige Zerlegung" in text and "Von 200 zufälligen Haltefolgen dieser Instanz lassen sich 0 (0,00 %)" in text
    assert ev.requests_text(lv.order) in text and ev.de(lv.order_cost) in text and ev.de(opt) in text and ev.signed_pct(ev.gap_percent(lv.order_cost, opt)) in text


def test_levels_verdict_with_a_stop_split(hand):
    s, inst = _inst()
    lv = ev.levels(inst, 0, 0, 50)
    # Seed 0 ist keine zulässige Haltefolge der Handinstanz; die Prüfung der Verzweigung mit Split baut die Ebene von Hand
    good = ev.Levels(tuple(range(1, 9)), M.solve(inst).cost, ((1, 2, 3, 4), (5, 6, 7, 8)), lv.order, lv.order_cost, lv.order_blocks, 50, 7)
    kind, text = ev.verdict_levels(inst, good)
    assert kind == "info" and "Die Haltefolge zerlegt sich in 2 Routen mit Länge 43,42 (0,0 % gegen das Optimum 43,42)" in text and "lassen sich 7 (14,00 %)" in text


def test_order_verdict_levels():
    s, inst = _inst()
    wl = M.limited_costs(inst)
    from afs_split import split_requests
    cost, blocks = split_requests(inst, [0, 1, 2, 3], wl)
    kind, text = ev.verdict_order(inst, [0, 1, 2, 3], cost, blocks)
    assert kind == "success" and "diese Folge liefert es." in text and "(1 2) ‖ (3 4)" in text and "43,42" in text
    cost, blocks = split_requests(inst, [0, 2, 1, 3], wl)
    kind, text = ev.verdict_order(inst, [0, 2, 1, 3], cost, blocks)
    assert kind == "info" and "diese Folge liefert es nicht." in text and "45,71" in text and "+5,3 %" in text and "3 Routen" in text


def test_rarity_verdict():
    s, inst = _inst(family=1, m=5, depot=0, Q=6, limit=50, seed=2)
    en = ev.enumerate_orders(inst)
    kind, text = ev.verdict_rarity(inst, en)
    assert kind == "info" and f"Von 120 Auftragsfolgen liefern {en.optimal} ({ev.pct(en.share)}) das Optimum {ev.de(en.opt)}" in text
    assert ev.pct(en.gap_mean) in text and ev.pct(en.gap_median) in text and ev.pct(en.gap_max) in text and "Jede dieser Folgen ist zulässig." in text


def test_methods_verdict():
    s, inst = _inst(family=1, m=6, depot=0, Q=6, limit=50, seed=3)
    cmp_ = ev.compare(inst, 5, 20, 0)
    kind, text = ev.verdict_methods(inst, cmp_)
    assert f"Optimum {ev.de(cmp_.opt)}" in text and "bestes von 5 Reihenfolgen" in text and "bestes von 20 Folgen" in text
    best = min((k for k in cmp_.results if k != "opt"), key=lambda k: (cmp_.results[k][0], k))
    assert ev.METHOD_LABEL[best] in text and kind == ("success" if ev.gap_percent(cmp_.results[best][0], cmp_.opt) <= C.TOL else "info")
    for key, (cost, routes) in cmp_.results.items():
        assert M.plan_is_valid(inst, [list(r) for r in routes]) and M.plan_length(inst, routes) == pytest.approx(cost, abs=1e-9)


def test_positions_verdict():
    s, inst = _inst()
    base, request, options, outside = ev.insertion_case(inst, 0, 0)
    kind, text = ev.verdict_positions(base, request, options)
    assert kind == "info" and f"Eine Route mit {len(base)} Halten hat {len(options)} Positionspaare" in text and f"für Auftrag {request + 1}" in text
    assert f"{sum(1 for o in options if o[2])} halten die Last, {sum(1 for o in options if o[3])} halten auch die Streckengrenze ein" in text and f"{len(base) + 1} Positionen je Halt" in text


def test_band_verdicts():
    for m in C.BAND_METHOD_SIZES:
        g = ev.method_gaps(m)
        kind, text = ev.verdict_bands(m)
        assert kind == "info" and f"{m} Aufträgen" in text and f"einmal {ev.pct(g['ins1']['mean'])}" in text and f"bestes von 10 Reihenfolgen {ev.pct(g['ins10']['mean'])}" in text
        assert f"Optimum in {g['rand100']['optimal']} von 20" in text and "Ein Lauf je Instanz" in text


def test_core_verdict():
    kind, text = ev.verdict_core()
    d, e, g8 = ev.dominance_stats(), ev.enum_stats(7), ev.method_gaps(8)
    assert kind == "info" and f"Haltefolgen: {d['stops_ok']} von {d['stops_n']} Instanzen" in text and f"Auftragsfolgen: {d['requests_ok']} von {d['requests_n']}" in text
    assert ev.pct(ev.feas_stats(4)["p_limit"], 2) in text and ev.pct(e["share_median"]) in text and ev.pct(g8["rand100"]["mean"]) in text and ev.pct(g8["ins1"]["mean"]) in text


def test_levels_are_deterministic():
    s, inst = _inst(family=1, m=5, depot=1, Q=6, limit=50, seed=4)
    a, b = ev.levels(inst, 3, 4, 100), ev.levels(inst, 3, 4, 100)
    assert a.stop_seq == b.stop_seq and a.order == b.order and a.sample_feasible == b.sample_feasible and a.order_cost == b.order_cost
