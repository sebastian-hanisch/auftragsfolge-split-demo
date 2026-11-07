"""Verfahren: Einfügen, nächster Nachbar auf Aufträgen, beste von k Auftragsfolgen mit Split; dazu die Einfügepositionen (Stück 10)."""

import math
import random

import afs_constants as C
import afs_model as M
import afs_split as SP

INF = math.inf


def insertion_options(inst: M.Instance, route, request: int):
    """Alle Positionspaare (a, b) mit a <= b, an denen Abholen von `request` vor Position a und Liefern vor Position b (nach dem Einfügen des Abholens) in die Route kommt:
    Liste von (a, b, kapazitätszulässig, ganz zulässig, Mehrlänge). Ganz zulässig: Last, Abholen vor Liefern und Streckengrenze."""
    base = M.route_length(inst, route)
    p, d = M.pickup(request), M.delivery(request)
    out = []
    for a in range(len(route) + 1):
        for b in range(a, len(route) + 1):
            cand = list(route[:a]) + [p] + list(route[a:b]) + [d] + list(route[b:])
            cap_ok = M.route_is_valid(inst, cand, check_limit=False)
            ok = cap_ok and M.route_length(inst, cand) <= inst.Lmax + C.TOL
            out.append((a, b, cap_ok, ok, M.route_length(inst, cand) - base))
    return out


def insertion_heuristic(inst: M.Instance, order):
    """Aufträge nacheinander an der billigsten zulässigen Stelle (Abholen und Liefern in derselben Route, Last und Streckengrenze eingehalten) einfügen, sonst neue Route.
    Gibt die Routen (Haltefolgen) zurück; Gleichstand: die zuerst gefundene Stelle (Route, dann a, dann b)."""
    routes: list[list[int]] = []
    for i in order:
        best = None
        for ri, r in enumerate(routes):
            for a, b, cap_ok, ok, delta in insertion_options(inst, r, i):
                if ok and (best is None or delta < best[0] - 1e-12):
                    best = (delta, ri, a, b)
        new_cost = M.route_length(inst, [M.pickup(i), M.delivery(i)])
        if best is None or new_cost < best[0] - 1e-12:
            routes.append([M.pickup(i), M.delivery(i)])
        else:
            _, ri, a, b = best
            r = routes[ri]
            routes[ri] = r[:a] + [M.pickup(i)] + r[a:b] + [M.delivery(i)] + r[b:]
    return routes


def nn_order(inst: M.Instance) -> list[int]:
    """Auftragsfolge nach dem nächsten Nachbarn: vom Depot, dann vom Lieferpunkt des letzten Auftrags zum nächsten Abholpunkt (Gleichstand: kleinere Nummer)."""
    D = M.distance_matrix(inst.pts)
    left, cur, order = set(range(inst.m)), 0, []
    while left:
        i = min(left, key=lambda k: (D[cur][M.pickup(k)], k))
        order.append(i)
        left.remove(i)
        cur = M.delivery(i)
    return order


def best_insertion(inst: M.Instance, k: int, rng: random.Random):
    """Bestes von k Einfügeläufen mit zufälliger Reihenfolge: (Länge des besten, alle Längen, Routen des besten)."""
    lengths, plans = [], []
    for _ in range(k):
        routes = insertion_heuristic(inst, SP.random_request_order(inst, rng))
        lengths.append(M.plan_length(inst, routes))
        plans.append(routes)
    j = min(range(k), key=lambda x: (lengths[x], x))
    return lengths[j], lengths, plans[j]


def best_orders(inst: M.Instance, k: int, rng: random.Random):
    """Bestes von k zufälligen Auftragsfolgen mit Split: (Kosten, Blöcke, die Folge)."""
    wl = M.limited_costs(inst)
    best = (INF, None, None)
    for _ in range(k):
        order = SP.random_request_order(inst, rng)
        cost, blocks = SP.split_requests(inst, order, wl)
        if cost < best[0] - 1e-12:
            best = (cost, blocks, order)
    return best


def blocks_to_routes(inst: M.Instance, blocks):
    """Routen (Haltefolgen) zu Blöcken von Aufträgen: die kürzeste Route der Menge."""
    t = M.raw_table(inst)
    return [t.routes[sum(1 << i for i in b)] for b in blocks]
