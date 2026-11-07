"""Eigenschaften, die für jede Instanz gelten: Zulässigkeit jeder Auftragsfolge, Monotonie, Invarianzen und der Fall ohne bindende Streckengrenze."""

import itertools
import random

import pytest

import afs_constants as C
import afs_heuristics as H
import afs_model as M
import afs_split as SP

INF = float("inf")
CASES = [(3, 1), (4, 2), (5, 3), (6, 4), (6, 5), (7, 6)]


@pytest.mark.parametrize("m,seed", CASES)
def test_every_request_order_is_feasible_and_not_below_the_optimum(m, seed):
    inst = M.make_instance(m, seed, corner=seed % 2 == 0)
    opt = M.solve(inst).cost
    wl = M.limited_costs(inst)
    rng = random.Random(seed)
    for _ in range(60):
        order = SP.random_request_order(inst, rng)
        cost, blocks = SP.split_requests(inst, order, wl)
        assert cost < INF and cost >= opt - 1e-9
        assert sorted(i for b in blocks for i in b) == list(range(m)) and [i for b in blocks for i in b] == order       # Blöcke decken die Folge der Reihe nach ab


@pytest.mark.parametrize("m,seed", CASES)
def test_removing_a_request_never_lengthens_the_shortest_route(m, seed):
    t = M.raw_table(M.make_instance(m, seed))
    for mask in range(1, 1 << m):
        for i in M.mask_requests(mask):
            assert t.w[mask ^ (1 << i)] <= t.w[mask] + 1e-9


@pytest.mark.parametrize("m,seed", CASES)
def test_the_optimum_is_never_below_the_one_route_through_everything_and_limits_only_add_cost(m, seed):
    inst = M.make_instance(m, seed)
    t = M.raw_table(inst)
    assert M.solve(inst).cost >= t.w[(1 << m) - 1] - 1e-9
    looser = M.with_limit(inst, inst.Lmax * 1.3)
    tighter = M.with_limit(inst, max(max(t.w[1 << i] for i in range(m)), inst.Lmax * 0.9))
    assert M.solve(looser).cost <= M.solve(inst).cost + 1e-9 <= M.solve(tighter).cost + 2e-9


@pytest.mark.parametrize("m,seed", CASES[:4])
def test_more_capacity_is_never_worse(m, seed):
    small = M.make_instance(m, seed, Q=4)
    big = M.Instance(small.pts, small.q, 8, small.Lmax)
    assert M.solve(big).cost <= M.solve(small).cost + 1e-9


@pytest.mark.parametrize("m,seed", CASES[:5])
def test_renumbering_the_requests_keeps_the_optimum_and_scaling_scales_it(m, seed):
    inst = M.make_instance(m, seed)
    perm = list(range(m))
    random.Random(seed).shuffle(perm)
    pts = [inst.pts[0]]
    for j in perm:
        pts += [inst.pts[M.pickup(j)], inst.pts[M.delivery(j)]]
    renum = M.Instance(tuple(pts), tuple(inst.q[j] for j in perm), inst.Q, inst.Lmax)
    assert M.solve(renum).cost == pytest.approx(M.solve(inst).cost, abs=1e-9)
    scaled = M.Instance(tuple((2 * x, 2 * y) for x, y in inst.pts), inst.q, inst.Q, 2 * inst.Lmax)
    assert M.solve(scaled).cost == pytest.approx(2 * M.solve(inst).cost, rel=1e-9)


@pytest.mark.parametrize("m,seed", CASES[:4])
def test_without_a_binding_limit_one_route_is_optimal_and_every_order_is_optimal(m, seed):
    """Die erste Fassung der Messung ohne Streckengrenze: die Frage der Zerlegung ist leer."""
    inst = M.make_instance(m, seed, limit_pct=100)
    sol = M.solve(inst)
    t = M.raw_table(inst)
    assert len(sol.routes) == 1 and sol.cost == pytest.approx(t.w[(1 << m) - 1], abs=1e-9)
    wl = M.limited_costs(inst)
    assert all(SP.split_requests(inst, p, wl)[0] == pytest.approx(sol.cost, abs=1e-9) for p in itertools.islice(itertools.permutations(range(m)), 200))


@pytest.mark.parametrize("m,seed", CASES[:4])
def test_the_concatenated_optimal_routes_split_back_to_the_optimum(m, seed):
    inst = M.make_instance(m, seed, corner=True)
    sol = M.solve(inst)
    seq = [s for r in sol.routes for s in r]
    cost, blocks = SP.split_stops(inst, seq)
    assert cost == pytest.approx(sol.cost, abs=1e-9)                        # die Dominanz, konstruktiv


def test_a_stop_sequence_without_a_feasible_block_has_no_split(hand):
    assert SP.split_stops(hand, (1, 3, 5, 7, 2, 4, 6, 8)) == (INF, None)


def test_determinism():
    a, b = M.make_instance(6, 17), M.make_instance(6, 17)
    assert a == b and a != M.make_instance(6, 18)
    r1, r2 = H.best_insertion(a, 5, random.Random(4)), H.best_insertion(b, 5, random.Random(4))
    assert r1[0] == r2[0] and r1[2] == r2[2]
    assert H.best_orders(a, 10, random.Random(4))[0] == H.best_orders(b, 10, random.Random(4))[0]


def test_the_limit_is_at_least_the_longest_single_route():
    for seed in range(8):
        inst = M.make_instance(5, seed, limit_pct=C.LIMIT_MIN)
        t = M.raw_table(inst)
        assert inst.Lmax >= max(t.w[1 << i] for i in range(5)) and all(M.limited_costs(inst)[1 << i] < INF for i in range(5))
