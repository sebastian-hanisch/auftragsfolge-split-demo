"""Handwerte (DEMO-PLAYBOOK §1b): die Handinstanz mit Wurzeln, Zulässigkeit von Routen, Blockpreise, Split und Einfügepositionen von Hand."""

import itertools
import math

import pytest

import afs_heuristics as H
import afs_model as M
import afs_split as SP

S5 = math.sqrt(5)
ROUTE = 15 + 3 * S5                       # (A1 L1 A2 L2): 3 + 3 + sqrt(45) + 3 + 6
OPT = 2 * ROUTE                           # 30 + 6 sqrt(5)
SPLIT_OTHER = ROUTE + 12 + 12             # eine Zweierroute und zwei einzelne (je 12)


def test_hand_numbers_by_roots():
    assert ROUTE == pytest.approx(21.7082, abs=5e-5) and OPT == pytest.approx(43.4164, abs=5e-5) and SPLIT_OTHER == pytest.approx(45.7082, abs=5e-5) and ROUTE <= 22


def test_routes_of_the_hand_instance(hand):
    assert M.route_length(hand, [1, 2, 3, 4]) == pytest.approx(ROUTE, abs=1e-12)                 # A1 L1 A2 L2
    assert M.route_length(hand, [1, 2, 5, 6]) == pytest.approx(24.0, abs=1e-12)                  # A1 L1 A3 L3: gegenüberliegende Achsen
    assert M.route_is_valid(hand, [1, 2, 3, 4]) and not M.route_is_valid(hand, [1, 2, 5, 6]) and M.route_is_valid(hand, [1, 2, 5, 6], check_limit=False)
    assert not M.route_is_valid(hand, [1, 3, 2, 4])                                              # A1 A2 L1 L2: Last 4 > 3
    assert not M.route_is_valid(hand, [2, 1, 3, 4])                                              # Liefern vor Abholen
    assert not M.route_is_valid(hand, [1, 2, 3])                                                 # Auftrag 2 nur abgeholt


def test_the_optimum_of_the_hand_instance(hand):
    sol = M.solve(hand)
    assert sol.cost == pytest.approx(OPT, abs=1e-9) and len(sol.routes) == 2
    assert sorted(sorted(M.mask_requests(b)) for b in sol.blocks) in ([[0, 1], [2, 3]], [[0, 3], [1, 2]])      # benachbarte Achsen je Route
    assert M.plan_is_valid(hand, sol.routes) and M.plan_length(hand, sol.routes) == pytest.approx(OPT, abs=1e-9)


def test_split_of_every_request_order_of_the_hand_instance(hand):
    wl = M.limited_costs(hand)
    costs = {p: SP.split_requests(hand, p, wl)[0] for p in itertools.permutations(range(4))}
    assert sum(1 for c in costs.values() if c == pytest.approx(OPT, abs=1e-9)) == 16
    assert sum(1 for c in costs.values() if c == pytest.approx(SPLIT_OTHER, abs=1e-9)) == 8
    assert costs[(0, 1, 2, 3)] == pytest.approx(OPT, abs=1e-9) and costs[(0, 2, 1, 3)] == pytest.approx(SPLIT_OTHER, abs=1e-9)    # Achsen 1, 3, 2, 4: gegenüberliegende zuerst
    assert SP.split_requests(hand, (0, 1, 2, 3), wl)[1] == ((0, 1), (2, 3))


def test_stop_sequences_of_the_hand_instance(hand):
    cost, blocks = SP.split_stops(hand, (1, 2, 3, 4, 5, 6, 7, 8))
    assert cost == pytest.approx(OPT, abs=1e-9) and blocks == ((1, 2, 3, 4), (5, 6, 7, 8))
    assert SP.split_stops(hand, (1, 3, 5, 7, 2, 4, 6, 8))[0] == math.inf                         # alle Abholungen zuerst: Last 8 > 3, kein Block zulässig


def test_two_requests_on_a_line(two):
    assert M.route_length(two, [1, 2, 3, 4]) == pytest.approx(8.0)
    assert M.route_is_valid(two, [1, 2, 3, 4]) and not M.route_is_valid(two, [1, 3, 2, 4])
    sol = M.solve(two)
    assert sol.cost == pytest.approx(8.0) and len(sol.routes) == 1 and sol.routes[0] == (1, 2, 3, 4)


def test_insertion_positions_by_hand(hand):
    options = H.insertion_options(hand, [1, 2], 1)            # Auftrag 2 in die Route (A1 L1)
    assert len(options) == 6                                  # (a, b) mit 0 <= a <= b <= 2
    ok = {(a, b) for a, b, cap, full, delta in options if full}
    assert ok == {(0, 0), (2, 2)} and sum(1 for o in options if o[2]) == 2
    for a, b, cap, full, delta in options:
        if full:
            assert delta == pytest.approx(ROUTE - 12.0, abs=1e-9) and delta == pytest.approx(3 + 3 * S5, abs=1e-9)


def test_insertion_heuristic_on_the_hand_instance(hand):
    routes = H.insertion_heuristic(hand, [0, 1, 2, 3])
    assert routes == [[3, 4, 1, 2], [7, 8, 5, 6]]                  # Auftrag 2 an der ersten gefundenen billigsten Stelle (a = b = 0)
    assert M.plan_is_valid(hand, routes) and M.plan_length(hand, routes) == pytest.approx(OPT, abs=1e-9)
