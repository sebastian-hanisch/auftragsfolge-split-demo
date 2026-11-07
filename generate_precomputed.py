"""Erzeugt afs_bands.json: die Bänder der Auftragsfolge-Demo (Stück 10 der Linie Tourenbildung).

Inhalt: (1) Zulässigkeit zufälliger Haltefolgen (m = 2, 3, 4, 5, 6, 8; 20 Instanzen mit je 500 Zufallsfolgen), mit und ohne Streckengrenze; (2) Aufzählung aller Auftragsfolgen (m = 4 bis 7, 12 Instanzen):
Anteil optimaler Folgen und Lücke zufälliger Folgen; (3) die Verfahren (m = 6, 7, 8; 20 Instanzen): Optimum, Einfügen (eine Reihenfolge, Mittel und bestes von 10), nächster Nachbar + Split, eine zufällige Auftragsfolge
+ Split, bestes von 100; (4) Dominanz: alle Haltefolgen (m = 4, 5 Instanzen) und alle Auftragsfolgen (m = 5, 20 Instanzen) gegen das exakte Optimum; (5) Einfügepositionen eines Auftrags in eine zufällige zulässige
Route mit k Aufträgen (k = 1 bis 5). Alle Instanzen deterministisch aus festen Seeds (Kapazität 6, Streckengrenze die Hälfte der kürzesten Gesamtroute). Es werden keine Zeiten gespeichert.

Aufruf (rechnet alles mit höchstens 12 Prozessen, einige Minuten):
    python generate_precomputed.py"""

import itertools
import json
import random
import statistics as st
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import afs_constants as C
import afs_heuristics as H
import afs_model as M
import afs_split as SP

TARGET = Path(__file__).with_name(C.BAND_FILE)
INF = float("inf")


def feas_seed(m: int, i: int) -> int:
    return 7000 + 100 * m + i


def enum_seed(m: int, i: int) -> int:
    return 200 + 50 * m + i


def method_seed(m: int, i: int) -> int:
    return 1000 * m + i


def dominance_stop_seed(i: int) -> int:
    return 400 + i


def dominance_req_seed(i: int) -> int:
    return 900 + i


def feas_job(args):
    m, i = args
    inst = M.make_instance(m, feas_seed(m, i), corner=i % 2 == 1, Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    rng = random.Random(feas_seed(m, i))
    lim = nolim = 0
    for _ in range(C.BAND_RANDOM_SEQS):
        seq = SP.random_stop_sequence(inst, rng)
        lim += SP.split_stops(inst, seq, True)[0] < INF
        nolim += SP.split_stops(inst, seq, False)[0] < INF
    return {"m": m, "i": i, "seqs": C.BAND_RANDOM_SEQS, "feasible_limit": lim, "feasible_nolimit": nolim}


def enum_job(args):
    m, i = args
    inst = M.make_instance(m, enum_seed(m, i), corner=False, Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    wl = M.limited_costs(inst)
    opt = M.solve(inst).cost
    vals = [SP.split_requests(inst, p, wl)[0] for p in itertools.permutations(range(m))]
    return {"m": m, "i": i, "opt": opt, "orders": len(vals), "optimal": sum(1 for v in vals if abs(v - opt) < 1e-9),
            "gap_mean": 100 * (st.mean(vals) / opt - 1), "gap_median": 100 * (st.median(vals) / opt - 1), "gap_max": 100 * (max(vals) / opt - 1)}


def methods_job(args):
    m, i = args
    inst = M.make_instance(m, method_seed(m, i), corner=i % 2 == 1, Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    sol = M.solve(inst)
    rng = random.Random(method_seed(m, i))
    _, lengths, _ = H.best_insertion(inst, C.KS_INSERT, rng)
    wl = M.limited_costs(inst)
    orders = [SP.random_request_order(inst, rng) for _ in range(C.KS_ORDERS)]
    costs = [SP.split_requests(inst, o, wl)[0] for o in orders]
    return {"m": m, "i": i, "seed": method_seed(m, i), "corner": i % 2 == 1, "opt": sol.cost, "routes": len(sol.routes), "lmax": inst.Lmax,
            "ins1": lengths[0], "ins_mean10": st.mean(lengths), "ins10": min(lengths), "nn": SP.split_requests(inst, H.nn_order(inst), wl)[0], "rand1": costs[0], "rand100": min(costs)}


def dominance_stops_job(i):
    inst = M.make_instance(C.BAND_DOMINANCE_STOPS_M, dominance_stop_seed(i), Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    opt = M.solve(inst).cost
    best, feas = INF, 0
    for p in itertools.permutations(range(1, 2 * inst.m + 1)):
        c = SP.split_stops(inst, p)[0]
        feas += c < INF
        best = min(best, c)
    return {"i": i, "opt": opt, "best": best, "feasible": feas, "perms": 40320}


def dominance_req_job(i):
    inst = M.make_instance(C.BAND_DOMINANCE_REQ_M, dominance_req_seed(i), Q=C.BAND_Q, limit_pct=C.BAND_LIMIT)
    wl = M.limited_costs(inst)
    opt = M.solve(inst).cost
    best = min(SP.split_requests(inst, p, wl)[0] for p in itertools.permutations(range(inst.m)))
    return {"i": i, "opt": opt, "best": best}


def position_job(k):
    """Einfügen eines Auftrags in eine zufällige zulässige Route mit k Aufträgen (Zufallsablauf unter Kapazität): Zahl der Positionspaare und der kapazitätszulässigen."""
    rng = random.Random(11 + k)
    total = cap = 0
    for _ in range(C.BAND_POSITION_ROUTES):
        inst = M.random_instance(k + 1, rng.randint(0, 10 ** 6), corner=False, Q=C.BAND_Q)
        route, load, todo, open_ = [], 0, list(range(k)), []
        while todo or open_:
            moves = [("p", i) for i in todo if load + inst.q[i] <= inst.Q] + [("d", i) for i in open_]
            kind, i = rng.choice(moves)
            if kind == "p":
                route.append(M.pickup(i))
                load += inst.q[i]
                todo.remove(i)
                open_.append(i)
            else:
                route.append(M.delivery(i))
                load -= inst.q[i]
                open_.remove(i)
        opts = H.insertion_options(inst, route, k)
        total += len(opts)
        cap += sum(1 for o in opts if o[2])
    return {"k": k, "routes": C.BAND_POSITION_ROUTES, "pairs": total, "capacity_ok": cap, "stops": 2 * k}


def main():
    with ProcessPoolExecutor(max_workers=12) as pool:
        feas = list(pool.map(feas_job, [(m, i) for m in C.BAND_FEAS_SIZES for i in range(20)]))
        enum = list(pool.map(enum_job, [(m, i) for m in C.BAND_ENUM_SIZES for i in range(C.BAND_ENUM_INSTANCES)]))
        meth = list(pool.map(methods_job, [(m, i) for m in C.BAND_METHOD_SIZES for i in range(C.BAND_METHOD_INSTANCES)]))
        dom_s = list(pool.map(dominance_stops_job, range(C.BAND_DOMINANCE_STOPS_N)))
        dom_r = list(pool.map(dominance_req_job, range(C.BAND_DOMINANCE_REQ_N)))
        pos = list(pool.map(position_job, C.BAND_POSITION_SIZES))
    meta = {"capacity": C.BAND_Q, "limit_percent": C.BAND_LIMIT, "random_seqs": C.BAND_RANDOM_SEQS, "ks": {"insert": C.KS_INSERT, "orders": C.KS_ORDERS},
            "seeds": "feas: 7000 + 100 m + i; enum: 200 + 50 m + i; methods: 1000 m + i; dominance stops: 400 + i; dominance requests: 900 + i"}
    TARGET.write_text(json.dumps({"meta": meta, "feas": feas, "enum": enum, "methods": meth, "dominance_stops": dom_s, "dominance_requests": dom_r, "positions": pos}, ensure_ascii=False), encoding="utf-8")
    print("geschrieben:", TARGET.name, len(feas), len(enum), len(meth), len(dom_s), len(dom_r), len(pos))


if __name__ == "__main__":
    main()
