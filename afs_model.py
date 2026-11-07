"""Modell und exakte Lösung: Abholen und Liefern mit Kapazität und Streckengrenze (Stück 10 der Linie Tourenbildung).

Ein Depot (Punkt 0), m Aufträge; Auftrag i hat den Abholpunkt 1 + 2i, den Lieferpunkt 2 + 2i und die Last q[i]. Eine Route beginnt und endet im Depot, jeder Auftrag wird ganz in einer Route bedient
(Abholen vor Liefern), die Last im Fahrzeug überschreitet nie Q, die Länge der Route nie die Streckengrenze Lmax. Ziel: kürzeste Gesamtlänge. Ohne Streckengrenze (und mit Kapazität für zwei Aufträge zugleich)
wäre eine einzige Route durch alle Aufträge optimal: die Frage der Zerlegung wäre leer.

Exakt: ein DP über den Zustand (Status je Auftrag: 0 offen, 1 abgeholt, 2 geliefert; letzter Halt) liefert für jede Auftragsmenge S die kürzeste Route w[S] (Kapazität eingehalten); eine Partitions-DP darüber
mit w[S] nur für Routen höchstens Lmax das Optimum. 3^m Zustände: bis m = 8 in Sekunden."""

import math
from dataclasses import dataclass
from functools import lru_cache
import random

import afs_constants as C

INF = math.inf


@dataclass(frozen=True)
class Instance:
    pts: tuple[tuple[float, float], ...]   # pts[0] = Depot, pts[1 + 2i] = Abholpunkt, pts[2 + 2i] = Lieferpunkt von Auftrag i
    q: tuple[int, ...]                     # Last je Auftrag
    Q: int                                 # Kapazität
    Lmax: float                            # Streckengrenze je Route (inf: keine)

    @property
    def m(self) -> int:
        return len(self.q)


@lru_cache(maxsize=512)
def distance_matrix(pts: tuple) -> tuple:
    return tuple(tuple(math.dist(a, b) for b in pts) for a in pts)


def pickup(i: int) -> int:
    return 1 + 2 * i


def delivery(i: int) -> int:
    return 2 + 2 * i


def request_of(stop: int) -> int:
    return (stop - 1) // 2


def hand_instance() -> Instance:
    return Instance(C.HAND_POINTS, C.HAND_LOAD, C.HAND_Q, C.HAND_LIMIT)


# ----------------------------------------------------------------------------------------------------------------------------------- Exakte Tabelle

@dataclass(frozen=True, eq=False)
class Table:
    """Kürzeste Route je Auftragsmenge (Bitmaske) ohne Streckengrenze: Kosten und Haltefolge."""
    w: tuple[float, ...]
    routes: tuple[tuple[int, ...], ...]


@lru_cache(maxsize=64)
def _raw_table(pts: tuple, q: tuple, Q: int) -> Table:
    m = len(q)
    D = distance_matrix(pts)
    pw = [3 ** i for i in range(m)]
    total = 3 ** m
    L = 2 * m + 1
    dp = [[INF] * L for _ in range(total)]
    par = [[-1] * L for _ in range(total)]            # kodiert (Vorgängerzustand * L + letzter Halt davor)
    dp[0][0] = 0.0
    stat = []
    loads = []
    for s in range(total):
        x, ld, row = s, 0, []
        for i in range(m):
            v = x % 3
            x //= 3
            row.append(v)
            if v == 1:
                ld += q[i]
        stat.append(row)
        loads.append(ld)
    for s in range(total):
        row, ld, stt = dp[s], loads[s], stat[s]
        for last in range(L):
            c = row[last]
            if c == INF:
                continue
            for i in range(m):
                if stt[i] == 0 and ld + q[i] <= Q:
                    nxt = 1 + 2 * i
                elif stt[i] == 1:
                    nxt = 2 + 2 * i
                else:
                    continue
                s2 = s + pw[i]
                v = c + D[last][nxt]
                if v < dp[s2][nxt]:
                    dp[s2][nxt] = v
                    par[s2][nxt] = s * L + last
    w = [INF] * (1 << m)
    routes: list[tuple[int, ...]] = [()] * (1 << m)
    w[0] = 0.0
    for mask in range(1, 1 << m):
        s = sum(2 * pw[i] for i in range(m) if mask >> i & 1)
        best, best_last = INF, -1
        for last in range(1, L):
            v = dp[s][last] + D[last][0]
            if v < best:
                best, best_last = v, last
        w[mask] = best
        if best < INF:
            stops, cur_s, cur_last = [], s, best_last
            while cur_last != 0:
                stops.append(cur_last)
                code = par[cur_s][cur_last]
                cur_s, cur_last = divmod(code, L)
            routes[mask] = tuple(reversed(stops))
    return Table(tuple(w), tuple(routes))


def raw_table(inst: Instance) -> Table:
    return _raw_table(inst.pts, inst.q, inst.Q)


def limited_costs(inst: Instance) -> list[float]:
    """Blockpreis je Auftragsmenge mit Streckengrenze: die kürzeste Route, wenn sie höchstens Lmax lang ist, sonst unendlich."""
    t = raw_table(inst)
    return [x if x <= inst.Lmax + C.TOL else INF for x in t.w]


@dataclass(frozen=True, eq=False)
class Solution:
    cost: float
    blocks: tuple[int, ...]                         # Auftragsmengen (Bitmasken) der Routen
    routes: tuple[tuple[int, ...], ...]             # Haltefolgen der Routen


def mask_requests(mask: int) -> tuple[int, ...]:
    return tuple(i for i in range(mask.bit_length()) if mask >> i & 1)


@lru_cache(maxsize=256)
def solve(inst: Instance) -> Solution:
    """Das Optimum: Partitions-DP über alle Auftragsmengen mit dem Blockpreis."""
    m = inst.m
    wl = limited_costs(inst)
    f = [INF] * (1 << m)
    choice = [0] * (1 << m)
    f[0] = 0.0
    for mask in range(1, 1 << m):
        low = mask & -mask
        sub = mask
        while sub:
            if sub & low and wl[sub] < INF and f[mask ^ sub] + wl[sub] < f[mask] - 1e-12:
                f[mask] = f[mask ^ sub] + wl[sub]
                choice[mask] = sub
            sub = (sub - 1) & mask
    blocks, mask = [], (1 << m) - 1
    while mask:
        blocks.append(choice[mask])
        mask ^= choice[mask]
    t = raw_table(inst)
    blocks.sort()
    return Solution(f[(1 << m) - 1], tuple(blocks), tuple(t.routes[b] for b in blocks))


# ----------------------------------------------------------------------------------------------------------------------------------- Zufallsinstanzen

def random_instance(m: int, seed: int, corner: bool = False, Q: int = C.DEFAULT_Q) -> Instance:
    """Deterministisch aus (m, Seed, Depotlage, Kapazität), ohne Streckengrenze: Koordinaten ganzzahlig 0 bis 100, Last 1 bis 3."""
    rnd = random.Random(seed)
    pts = [(0.0, 0.0) if corner else (50.0, 50.0)]
    q = []
    for _ in range(m):
        pts.append((float(rnd.randint(0, 100)), float(rnd.randint(0, 100))))
        pts.append((float(rnd.randint(0, 100)), float(rnd.randint(0, 100))))
        q.append(rnd.randint(1, C.LOAD_MAX))
    return Instance(tuple(pts), tuple(q), Q, INF)


def make_instance(m: int, seed: int, corner: bool = False, Q: int = C.DEFAULT_Q, limit_pct: int = C.DEFAULT_LIMIT) -> Instance:
    """Wie `random_instance`, mit Streckengrenze = limit_pct Prozent der kürzesten Route über alle Aufträge, mindestens die längste Einzelroute."""
    inst = random_instance(m, seed, corner, Q)
    t = raw_table(inst)
    single = max(t.w[1 << i] for i in range(m))
    lmax = max(limit_pct / 100.0 * t.w[(1 << m) - 1], single) + 1e-9
    return Instance(inst.pts, inst.q, inst.Q, lmax)


def with_limit(inst: Instance, lmax: float) -> Instance:
    return Instance(inst.pts, inst.q, inst.Q, lmax)


# ----------------------------------------------------------------------------------------------------------------------------------- Prüfer

def route_length(inst: Instance, stops) -> float:
    D = distance_matrix(inst.pts)
    if not stops:
        return 0.0
    return D[0][stops[0]] + sum(D[a][b] for a, b in zip(stops, stops[1:])) + D[stops[-1]][0]


def route_is_valid(inst: Instance, stops, check_limit: bool = True) -> bool:
    """Unabhängiger Prüfer: jeder Halt höchstens einmal, beide Halte jedes bedienten Auftrags, Abholen vor Liefern, Last höchstens Q, Länge höchstens Lmax."""
    if len(set(stops)) != len(stops):
        return False
    load, picked, done = 0, set(), set()
    for s in stops:
        i = request_of(s)
        if s % 2 == 1:
            if i in picked:
                return False
            picked.add(i)
            load += inst.q[i]
            if load > inst.Q:
                return False
        else:
            if i not in picked or i in done:
                return False
            done.add(i)
            load -= inst.q[i]
    if picked != done:
        return False
    return not check_limit or route_length(inst, stops) <= inst.Lmax + C.TOL


def plan_is_valid(inst: Instance, routes, check_limit: bool = True) -> bool:
    """Jeder Auftrag in genau einer Route, jede Route gültig."""
    served = sorted(request_of(s) for r in routes for s in r if s % 2 == 1)
    return served == list(range(inst.m)) and all(route_is_valid(inst, r, check_limit) for r in routes)


def plan_length(inst: Instance, routes) -> float:
    return sum(route_length(inst, r) for r in routes)
