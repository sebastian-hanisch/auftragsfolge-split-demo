"""Die Bänder: Aufbau, Vollständigkeit, Stichproben gegen eine frische Rechnung mit denselben Funktionen und unabhängige Gegenproben (es werden nie Zeiten gespeichert oder geprüft)."""

import itertools

import pytest

import afs_constants as C
import afs_evaluation as ev
import afs_model as M
import afs_split as SP
import generate_precomputed as G

B = ev.load_bands()


def test_counts():
    assert len(B["feas"]) == 20 * len(C.BAND_FEAS_SIZES) and {r["m"] for r in B["feas"]} == set(C.BAND_FEAS_SIZES)
    assert len(B["enum"]) == C.BAND_ENUM_INSTANCES * len(C.BAND_ENUM_SIZES) and {r["m"] for r in B["enum"]} == set(C.BAND_ENUM_SIZES)
    assert len(B["methods"]) == C.BAND_METHOD_INSTANCES * len(C.BAND_METHOD_SIZES) and {r["m"] for r in B["methods"]} == set(C.BAND_METHOD_SIZES)
    assert len(B["dominance_stops"]) == C.BAND_DOMINANCE_STOPS_N and len(B["dominance_requests"]) == C.BAND_DOMINANCE_REQ_N and [r["k"] for r in B["positions"]] == list(C.BAND_POSITION_SIZES)
    assert not any("seconds" in key or "time" in key for rows in (B["feas"], B["enum"], B["methods"]) for r in rows for key in r)           # keine Zeiten in den Bändern


def test_the_feasible_counts_are_consistent():
    for r in B["feas"]:
        assert 0 <= r["feasible_limit"] <= r["feasible_nolimit"] <= r["seqs"] == C.BAND_RANDOM_SEQS                      # mit Streckengrenze nie mehr zulässige Folgen als ohne
    p = [ev.feas_stats(m)["p_nolimit"] for m in C.BAND_FEAS_SIZES]
    assert p == sorted(p, reverse=True)                                                                                    # je mehr Aufträge, desto kleiner der Anteil


def test_method_rows_are_ordered_and_never_below_the_optimum():
    for r in B["methods"]:
        assert r["ins1"] >= r["opt"] - 1e-9 and r["ins10"] >= r["opt"] - 1e-9 and r["ins10"] <= r["ins1"] + 1e-9 and r["ins10"] <= r["ins_mean10"] + 1e-9
        assert r["nn"] >= r["opt"] - 1e-9 and r["rand100"] >= r["opt"] - 1e-9 and r["rand100"] <= r["rand1"] + 1e-9


def test_enumeration_rows():
    for r in B["enum"]:
        n = 1
        for k in range(2, r["m"] + 1):
            n *= k
        assert r["orders"] == n and 1 <= r["optimal"] <= n and r["gap_max"] >= r["gap_mean"] >= -1e-9


def test_dominance_rows():
    assert all(abs(r["best"] - r["opt"]) < 1e-9 for r in B["dominance_stops"]) and all(abs(r["best"] - r["opt"]) < 1e-9 for r in B["dominance_requests"])
    assert all(r["perms"] == 40320 and 0 <= r["feasible"] <= r["perms"] for r in B["dominance_stops"])


def test_samples_are_reproduced_exactly():
    for args in ((4, 0), (3, 7)):
        row = next(r for r in B["feas"] if (r["m"], r["i"]) == args)
        assert G.feas_job(args) == row
    for args in ((5, 0), (6, 2)):
        row = next(r for r in B["enum"] if (r["m"], r["i"]) == args)
        fresh = G.enum_job(args)
        assert fresh["optimal"] == row["optimal"] and fresh["opt"] == pytest.approx(row["opt"], abs=1e-9) and fresh["gap_mean"] == pytest.approx(row["gap_mean"], abs=1e-9)
    for args in ((6, 3), (7, 0), (8, 5)):
        row = next(r for r in B["methods"] if (r["m"], r["i"]) == args)
        fresh = G.methods_job(args)
        assert all(fresh[k] == pytest.approx(row[k], abs=1e-9) for k in ("opt", "ins1", "ins_mean10", "ins10", "nn", "rand1", "rand100", "lmax"))
    row = next(r for r in B["dominance_requests"] if r["i"] == 3)
    assert G.dominance_req_job(3) == row
    assert G.position_job(2) == next(r for r in B["positions"] if r["k"] == 2)


def test_a_method_row_against_an_independent_brute_force():
    row = next(r for r in B["methods"] if (r["m"], r["i"]) == (6, 0))
    inst = M.make_instance(6, G.method_seed(6, 0), corner=False, Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    wl = M.limited_costs(inst)
    best = min(SP.split_requests(inst, p, wl)[0] for p in itertools.permutations(range(6)))
    assert best == pytest.approx(row["opt"], abs=1e-9) and row["rand100"] >= row["opt"] - 1e-9


def test_position_rows_follow_the_quadratic_law():
    for r in B["positions"]:
        k = r["k"]
        assert r["pairs"] == r["routes"] * (2 * k + 1) * (2 * k + 2) // 2 and r["stops"] == 2 * k and 0 < r["capacity_ok"] <= r["pairs"]
