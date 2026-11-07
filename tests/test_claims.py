"""Jede Zahl der README und der Preset-Hilfen wird aus den Bändern beziehungsweise der Rechnung nachgerechnet und muss im Text stehen (DEMO-PLAYBOOK §1b). Die Bänder enthalten keine Zeiten."""

import itertools
import json
import math
import statistics as st
from pathlib import Path

import afs_constants as C
import afs_evaluation as ev
import afs_model as M
import afs_split as SP

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
B = json.loads((ROOT / C.BAND_FILE).read_text(encoding="utf-8"))


def d(x, digits=2):
    return f"{x:.{digits}f}".replace(".", ",")


def p(x, digits=1):
    return d(x, digits) + " %"


def gap(cost, opt):
    return 0.0 if abs(cost - opt) < 1e-9 else 100.0 * (cost / opt - 1.0)


def test_feasibility_table():
    for m in C.BAND_FEAS_SIZES:
        rows = [r for r in B["feas"] if r["m"] == m]
        seqs, lim, nolim = sum(r["seqs"] for r in rows), sum(r["feasible_limit"] for r in rows), sum(r["feasible_nolimit"] for r in rows)
        row = f"| {m} | {p(100 * lim / seqs, 2)} ({lim} von {seqs}) | {p(100 * nolim / seqs, 2)} ({nolim} von {seqs}) |"
        assert row in README, row
    assert [ev.feas_stats(m)["limit"] for m in (2, 3, 4, 5, 6, 8)] == [821, 106, 12, 2, 1, 0]


def test_enumeration_table():
    for m in C.BAND_ENUM_SIZES:
        rows = [r for r in B["enum"] if r["m"] == m]
        shares = [100.0 * r["optimal"] / r["orders"] for r in rows]
        row = (f"| {m} | {rows[0]['orders']} | {p(st.median(shares))} | {p(min(shares))} / {p(max(shares))} | {p(st.mean(r['gap_mean'] for r in rows))} | {p(st.median(r['gap_median'] for r in rows))} |")
        assert row in README, row
    assert [r["orders"] for r in B["enum"] if r["i"] == 0] == [24, 120, 720, 5040]


def test_method_tables():
    labels = (("ins1", "Einfügen, eine Reihenfolge"), ("ins_mean10", "Einfügen, Mittel von 10 Reihenfolgen"), ("ins10", "Einfügen, bestes von 10"), ("nn", "Nächster Nachbar + Split"),
              ("rand1", "Eine Auftragsfolge + Split"), ("rand100", "Bestes von 100 Auftragsfolgen + Split"))
    for m in C.BAND_METHOD_SIZES:
        rows = [r for r in B["methods"] if r["m"] == m]
        assert len(rows) == 20 and f"**{m} Aufträge, 20 Instanzen:**" in README
        for key, label in labels:
            g = [gap(r[key], r["opt"]) for r in rows]
            line = f"| {label} | {p(st.mean(g))} | {p(st.median(g))} | {p(max(g))} | {sum(1 for x in g if x < 1e-6)} von 20 |"
            assert line in README, line
    rows8 = [r for r in B["methods"] if r["m"] == 8]
    g100 = [gap(r["rand100"], r["opt"]) for r in rows8]
    g1 = [gap(r["ins1"], r["opt"]) for r in rows8]
    text = f"das beste von 100 zufälligen Auftragsfolgen + Split liegt {p(st.mean(g100))} über dem Optimum und trifft es in {sum(1 for x in g100 if x < 1e-6)} von 20 Instanzen"
    assert text in README and f"Einfügen in einer Reihenfolge liegt bei 8 Aufträgen {p(st.mean(g1))} über dem Optimum" in README


def test_position_table():
    for r in B["positions"]:
        k = r["k"]
        row = f"| {k} | {2 * k} | {d(r['pairs'] / r['routes'], 1)} | {d(r['capacity_ok'] / r['routes'], 1)} | {p(100 * r['capacity_ok'] / r['pairs'], 0)} |"
        assert row in README, row
    assert [r["pairs"] / r["routes"] for r in B["positions"]] == [6.0, 15.0, 28.0, 45.0, 66.0]


def test_dominance_sentence():
    ds, dr = B["dominance_stops"], B["dominance_requests"]
    ok_s = sum(1 for r in ds if abs(r["best"] - r["opt"]) < 1e-9)
    ok_r = sum(1 for r in dr if abs(r["best"] - r["opt"]) < 1e-9)
    assert (ok_s, len(ds), ok_r, len(dr)) == (5, 5, 20, 20)
    assert f"für alle 40320 Haltefolgen von 4 Aufträgen in {ok_s} von {len(ds)} Instanzen, für alle Auftragsfolgen von 5 Aufträgen in {ok_r} von {len(dr)} Instanzen" in README
    assert f"waren in den {len(ds)} Instanzen zusammen nur {sum(r['feasible'] for r in ds)} zerlegbar" in README


def test_the_case_without_a_limit():
    ok = tot = 0
    for m in (5, 6):
        for seed in range(1, 7):
            inst = M.make_instance(m, seed, limit_pct=100)
            assert len(M.solve(inst).routes) == 1
            wl = M.limited_costs(inst)
            opt = M.solve(inst).cost
            for perm in itertools.permutations(range(m)):
                ok += abs(SP.split_requests(inst, perm, wl)[0] - opt) < 1e-9
                tot += 1
    assert f"und {ok} von {tot} Auftragsfolgen (12 Instanzen mit 5 und 6 Aufträgen) liefern das Optimum" in README and ok == tot


def test_the_hand_instance_numbers():
    hand = M.hand_instance()
    sol = M.solve(hand)
    assert abs(sol.cost - (30 + 6 * math.sqrt(5))) < 1e-9
    assert f"Optimum 30 + 6√5 = {d(sol.cost)} mit zwei Routen; 16 der 24 Auftragsfolgen liefern es, die übrigen 8 kosten 45,71" in README
    wl = M.limited_costs(hand)
    vals = [SP.split_requests(hand, q, wl)[0] for q in itertools.permutations(range(4))]
    assert sum(1 for v in vals if abs(v - sol.cost) < 1e-9) == 16 and d(max(vals)) == "45,71" and len(vals) == 24


def test_the_corrections_of_the_plan_section():
    f = {m: [r for r in B["feas"] if r["m"] == m] for m in (2, 3, 4, 5, 6, 8)}

    def share(m, key):
        rows = f[m]
        return 100.0 * sum(r[key] for r in rows) / sum(r["seqs"] for r in rows)

    no = f"ohne {p(share(2, 'feasible_nolimit'))} / {p(share(3, 'feasible_nolimit'))} / {p(share(4, 'feasible_nolimit'))} / {p(share(5, 'feasible_nolimit'))} / {p(share(6, 'feasible_nolimit'), 2)} / {p(share(8, 'feasible_nolimit'), 2)}"
    yes = f"mit {p(share(2, 'feasible_limit'))} / {p(share(3, 'feasible_limit'))} / {p(share(4, 'feasible_limit'), 2)} / {p(share(5, 'feasible_limit'), 2)} / {p(share(6, 'feasible_limit'), 2)} / {p(share(8, 'feasible_limit'), 2)}"
    assert no in README and yes in README
    rows8 = [r for r in B["methods"] if r["m"] == 8]
    g100 = [gap(r["rand100"], r["opt"]) for r in rows8]
    g10 = [gap(r["ins10"], r["opt"]) for r in rows8]
    assert f"geben {p(st.mean(g100))} ({sum(1 for x in g100 if x < 1e-6)} von 20) und {p(st.mean(g10))}" in README
    shares = " / ".join(p(100.0 * r["capacity_ok"] / r["pairs"], 0) for r in B["positions"])
    assert f"die Bänder mit 150 Routen geben {shares}" in README


# --- Presets -----------------------------------------------------------------------------------------------------------------------------

def _settings(name):
    q = C.PRESETS[name]
    return ev.Settings(q["family"], q["m"], q["depot"], q["Q"], q["limit"], q["seed"])


def test_hand_preset():
    name = "Das Handbeispiel (4 Aufträge)"
    h = C.PRESET_HELP[name]
    inst = ev.build_instance(_settings(name))
    sol = M.solve(inst)
    assert d(sol.cost) == "43,42" and len(sol.routes) == 2 and inst.Q == 3 and inst.Lmax == 22.0 and list(inst.q) == [2, 2, 2, 2]
    for text in ("Kapazität 3", "Streckengrenze 22", "30 + 6√5 = 43,42", "zwei Routen", "16 der 24", "45,71"):
        assert text in h, text


def test_halt_preset():
    name = "Haltefolge ohne Zerlegung (6 Aufträge)"
    s = _settings(name)
    inst = ev.build_instance(s)
    lv = ev.levels(inst, 1, 1, 1000)
    opt = M.solve(inst).cost
    assert lv.sample_feasible == 0 and lv.stop_blocks is None and ev.requests_text(lv.order) == "2 5 1 6 4 3" and len(lv.order_blocks) == 5
    assert (d(lv.order_cost), d(opt), p(gap(lv.order_cost, opt))) == ("596,75", "549,31", "8,6 %")
    for text in ("Seed 3", "1000 zufälligen Haltefolgen", "keine in zulässige Routen", "2 5 1 6 4 3", "5 Routen", "596,75", "8,6 %", "549,31"):
        assert text in C.PRESET_HELP[name], text


def test_rarity_preset():
    name = "Das Optimum ist selten (7 Aufträge)"
    inst = ev.build_instance(_settings(name))
    en = ev.enumerate_orders(inst)
    assert (en.optimal, len(en.costs), p(en.share), p(en.gap_mean), p(en.gap_median), p(en.gap_max), d(en.opt), len(M.solve(inst).routes)) == (144, 5040, "2,9 %", "24,1 %", "26,1 %", "47,0 %", "651,81", 3)
    for text in ("Seed 6", "651,81", "3 Routen", "5040", "144 (2,9 %)", "24,1 %", "26,1 %", "47,0 %"):
        assert text in C.PRESET_HELP[name], text


def test_insertion_preset():
    name = "Einfügen gegen Folge (7 Aufträge)"
    inst = ev.build_instance(_settings(name))
    cmp_ = ev.compare(inst, 10, 100, 0)
    g = {k: gap(v[0], cmp_.opt) for k, v in cmp_.results.items()}
    assert d(cmp_.opt) == "532,08" and (p(g["ins1"]), p(g["nn"]), p(g["rand1"])) == ("20,0 %", "51,7 %", "38,5 %") and g["insk"] == 0.0 and g["randk"] == 0.0
    for text in ("Seed 11", "532,08", "20,0 %", "51,7 %", "38,5 %", "beste von 10", "beste von 100"):
        assert text in C.PRESET_HELP[name], text
