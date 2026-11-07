"""Randfälle: ein und zwei Aufträge, Kapazität gleich größte Last, Streckengrenze gleich längste Einzelroute, Einzelrouten, Formate."""

import pytest

import afs_constants as C
import afs_evaluation as ev
import afs_heuristics as H
import afs_model as M
import afs_split as SP


def test_one_request():
    inst = M.make_instance(1, 3)
    sol = M.solve(inst)
    assert len(sol.routes) == 1 and sol.cost == pytest.approx(M.route_length(inst, [1, 2])) and sol.blocks == (1,)
    assert SP.split_requests(inst, [0])[0] == pytest.approx(sol.cost) and SP.split_stops(inst, [1, 2])[0] == pytest.approx(sol.cost)
    assert SP.split_stops(inst, [2, 1]) == (float("inf"), None)               # Liefern vor Abholen


def test_two_requests_and_the_smallest_ui_size():
    inst = M.make_instance(C.M_MIN, 5)
    assert inst.m == 2 and M.solve(inst).cost > 0
    live = ev.compare(inst, 3, 5, 0)
    assert live.results["opt"][0] == pytest.approx(M.solve(inst).cost) and all(M.plan_is_valid(inst, [list(r) for r in v[1]]) for v in live.results.values())


def test_capacity_equal_to_the_largest_load_and_the_smallest_limit():
    assert C.Q_MIN >= C.LOAD_MAX
    inst = M.make_instance(5, 2, Q=C.LOAD_MAX, limit_pct=C.LIMIT_MIN)
    sol = M.solve(inst)
    assert M.plan_is_valid(inst, sol.routes) and all(M.route_length(inst, r) <= inst.Lmax + 1e-9 for r in sol.routes)
    singles = sum(M.raw_table(inst).w[1 << i] for i in range(5))
    assert sol.cost <= singles + 1e-9                                         # jeder Auftrag allein ist immer zulässig


def test_every_request_alone_when_the_limit_forces_it():
    inst = M.make_instance(4, 9)
    t = M.raw_table(inst)
    tight = M.with_limit(inst, max(t.w[1 << i] for i in range(4)) + 1e-9)
    two_route_min = min(t.w[(1 << i) | (1 << j)] for i in range(4) for j in range(i + 1, 4))
    sol = M.solve(tight)
    assert M.plan_is_valid(tight, sol.routes)
    if two_route_min > tight.Lmax:
        assert len(sol.routes) == 4 and sol.cost == pytest.approx(sum(t.w[1 << i] for i in range(4)))


def test_insertion_into_an_empty_plan_and_the_single_route_case():
    inst = M.make_instance(3, 4)
    assert H.insertion_heuristic(inst, []) == []
    one = M.make_instance(3, 4, limit_pct=100)
    base, request, options, outside = ev.insertion_case(one, 0, 0)
    assert len(base) == 4 and outside == [request] and len(options) == (len(base) + 1) * (len(base) + 2) // 2


def test_insertion_case_wraps_the_indices():
    inst = M.hand_instance()
    base0, r0, opts0, out0 = ev.insertion_case(inst, 0, 0)
    base_wrap, r_wrap, opts_wrap, _ = ev.insertion_case(inst, 2, len(out0))
    assert base_wrap == base0 and r_wrap == r0 and len(opts0) == len(opts_wrap)


def test_order_with_rest_and_formats():
    assert ev.order_with_rest([2, 0], 4) == [2, 0, 1, 3] and ev.order_with_rest([], 3) == [0, 1, 2] and ev.order_with_rest([1, 1], 3) == [1, 0, 2]
    assert ev.de(3.14159) == "3,14" and ev.pct(12.345) == "12,3 %" and ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(2.5) == "+2,5 %" and ev.signed_pct(-2.5) == "−2,5 %"
    assert ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz" and ev.instances_word(8) == "8 Instanzen"
    assert ev.gap_percent(10.0, 10.0) == 0.0 and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0) and ev.requests_text([0, 2]) == "1 3"
    assert SP.stops_text([1, 2, 5, 6]) == "A1 L1 A3 L3"


def test_the_enumeration_is_limited():
    with pytest.raises(ValueError):
        ev.enumerate_orders(M.make_instance(C.ENUM_MAX + 1, 1))


def test_the_default_insertion_choice_maximizes_the_feasible_positions():
    for inst in (M.hand_instance(), M.make_instance(6, 3), M.make_instance(5, 8, limit_pct=100)):
        r, q = ev.default_insertion_choice(inst)
        _, _, options, _ = ev.insertion_case(inst, r, q)
        best = (sum(1 for o in options if o[3]), sum(1 for o in options if o[2]))
        for rr in range(len(M.solve(inst).routes)):
            outside = ev.insertion_case(inst, rr, 0)[3]
            for qq in range(len(outside)):
                _, _, opts, _ = ev.insertion_case(inst, rr, qq)
                assert (sum(1 for o in opts if o[3]), sum(1 for o in opts if o[2])) <= best
        assert ev.default_insertion_choice(inst, r)[0] == r
