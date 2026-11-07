"""Orakel (ORACLE-PLAYBOOK §5): ein unabhängiger Rechenweg gegen die exakte Lösung, die Dominanz und jedes Verfahren.

Das Orakel zählt alle Zerlegungen der Aufträge in Gruppen auf und nimmt je Gruppe die kürzeste zulässige Route aus allen Reihenfolgen der Halte (Aufzählung aller Permutationen, eigener Prüfer)."""

import itertools
import math

import pytest

import afs_heuristics as H
import afs_model as M
import afs_split as SP

INF = math.inf


def _valid(inst, stops, limit):
    load, seen = 0, set()
    for s in stops:
        i = (s - 1) // 2
        if s % 2 == 1:
            seen.add(i)
            load += inst.q[i]
            if load > inst.Q:
                return False
        else:
            if i not in seen:
                return False
            load -= inst.q[i]
    return not limit or _len(inst, stops) <= inst.Lmax + 1e-9


def _len(inst, stops):
    pts = [inst.pts[0]] + [inst.pts[s] for s in stops] + [inst.pts[0]]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def brute_route(inst, requests, limit=True):
    """Kürzeste zulässige Route durch genau diese Aufträge: alle Permutationen der Halte."""
    stops = [s for i in requests for s in (M.pickup(i), M.delivery(i))]
    best = INF
    for p in itertools.permutations(stops):
        if _valid(inst, p, limit):
            best = min(best, _len(inst, p))
    return best


def _partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _partitions(rest):
        yield [[first]] + part
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]


def brute_optimum(inst):
    cache = {}
    best = INF
    for part in _partitions(list(range(inst.m))):
        total = 0.0
        for g in part:
            key = tuple(sorted(g))
            if key not in cache:
                cache[key] = brute_route(inst, key)
            total += cache[key]
            if total >= best:
                break
        best = min(best, total)
    return best


def test_brute_force_oracle_on_the_hand_instance(hand):
    assert brute_optimum(hand) == pytest.approx(30 + 6 * math.sqrt(5), abs=1e-9)


@pytest.mark.parametrize("m,seed,corner,limit", [(2, 1, False, 50), (3, 2, True, 50), (3, 3, False, 40), (3, 4, False, 60), (3, 5, True, 35)])
def test_the_exact_solution_equals_the_enumeration(m, seed, corner, limit):
    inst = M.make_instance(m, seed, corner=corner, limit_pct=limit)
    sol = M.solve(inst)
    assert sol.cost == pytest.approx(brute_optimum(inst), abs=1e-9)
    assert M.plan_is_valid(inst, sol.routes) and M.plan_length(inst, sol.routes) == pytest.approx(sol.cost, abs=1e-9)
    t = M.raw_table(inst)
    for mask in range(1, 1 << m):
        reqs = M.mask_requests(mask)
        assert t.w[mask] == pytest.approx(brute_route(inst, reqs, limit=False), abs=1e-9)
        assert M.route_length(inst, t.routes[mask]) == pytest.approx(t.w[mask], abs=1e-9) and M.route_is_valid(inst, t.routes[mask], check_limit=False)


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_dominance_on_both_levels_for_three_requests(seed):
    inst = M.make_instance(3, seed, corner=seed % 2 == 0)
    opt = M.solve(inst).cost
    wl = M.limited_costs(inst)
    assert min(SP.split_requests(inst, p, wl)[0] for p in itertools.permutations(range(3))) == pytest.approx(opt, abs=1e-9)
    assert min(SP.split_stops(inst, p)[0] for p in itertools.permutations(range(1, 7))) == pytest.approx(opt, abs=1e-9)


def test_dominance_on_the_hand_instance_for_requests(hand):
    wl = M.limited_costs(hand)
    assert min(SP.split_requests(hand, p, wl)[0] for p in itertools.permutations(range(4))) == pytest.approx(M.solve(hand).cost, abs=1e-9)


@pytest.mark.parametrize("m,seed", [(4, 1), (5, 2), (6, 3), (7, 4), (7, 5)])
def test_every_method_gives_a_valid_plan_not_below_the_optimum(m, seed):
    inst = M.make_instance(m, seed, corner=seed % 2 == 1)
    opt = M.solve(inst).cost
    import random
    plans = {"ins": H.insertion_heuristic(inst, list(range(m))), "ins_rev": H.insertion_heuristic(inst, list(reversed(range(m)))), "insk": H.best_insertion(inst, 5, random.Random(1))[2]}
    cost_nn, blocks_nn = SP.split_requests(inst, H.nn_order(inst))
    plans["nn"] = H.blocks_to_routes(inst, blocks_nn)
    cost_b, blocks_b, _ = H.best_orders(inst, 20, random.Random(2))
    plans["orders"] = H.blocks_to_routes(inst, blocks_b)
    for name, routes in plans.items():
        assert M.plan_is_valid(inst, [list(r) for r in routes]), name
        assert M.plan_length(inst, routes) >= opt - 1e-9, name
    assert M.plan_length(inst, plans["nn"]) == pytest.approx(cost_nn, abs=1e-9) and M.plan_length(inst, plans["orders"]) == pytest.approx(cost_b, abs=1e-9)


def test_the_checker_rejects_broken_plans(hand):
    assert not M.plan_is_valid(hand, [[1, 2, 3, 4], [5, 6, 7, 8], [1, 2]])           # Auftrag 1 doppelt
    assert not M.plan_is_valid(hand, [[1, 2, 3, 4], [5, 6]])                          # Aufträge 3 und 4 fehlen: 2 und 3 sind bedient
    assert not M.plan_is_valid(hand, [[1, 2, 5, 6], [3, 4], [7, 8]])                  # erste Route länger als die Streckengrenze
    assert M.plan_is_valid(hand, [[1, 2, 5, 6], [3, 4], [7, 8]], check_limit=False)
