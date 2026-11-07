"""Formate, Bänder, Live-Rechnungen und Verdikte. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import itertools
import json
import random
import statistics as st
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import afs_constants as C
import afs_heuristics as H
import afs_model as M
import afs_split as SP

INF = float("inf")


@dataclass(frozen=True)
class Settings:
    family: int = C.DEFAULT_FAMILY
    m: int = C.DEFAULT_M
    depot: int = C.DEFAULT_DEPOT
    Q: int = C.DEFAULT_Q
    limit: int = C.DEFAULT_LIMIT
    seed: int = C.DEFAULT_SEED


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def gap_percent(cost: float, reference: float) -> float:
    if reference <= 0 or abs(cost - reference) <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def requests_text(order) -> str:
    return " ".join(str(i + 1) for i in order)


def blocks_text(blocks) -> str:
    return " ‖ ".join("(" + requests_text(b) + ")" for b in blocks)


def build_instance(s: Settings) -> M.Instance:
    if s.family == C.HAND_FAMILY:
        return M.hand_instance()
    return M.make_instance(s.m, s.seed, corner=s.depot == 1, Q=s.Q, limit_pct=s.limit)


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

@lru_cache(maxsize=1)
def load_bands() -> dict:
    path = Path(__file__).with_name(C.BAND_FILE)
    if not path.exists():
        return {"meta": {}, "feas": [], "enum": [], "methods": [], "dominance_stops": [], "dominance_requests": [], "positions": []}
    return json.loads(path.read_text(encoding="utf-8"))


def feas_stats(m: int) -> dict:
    rows = [r for r in load_bands()["feas"] if r["m"] == m]
    seqs = sum(r["seqs"] for r in rows)
    lim, nolim = sum(r["feasible_limit"] for r in rows), sum(r["feasible_nolimit"] for r in rows)
    return {"instances": len(rows), "seqs": seqs, "limit": lim, "nolimit": nolim, "p_limit": 100.0 * lim / seqs if seqs else 0.0, "p_nolimit": 100.0 * nolim / seqs if seqs else 0.0}


def enum_stats(m: int) -> dict:
    rows = [r for r in load_bands()["enum"] if r["m"] == m]
    shares = [100.0 * r["optimal"] / r["orders"] for r in rows]
    return {"instances": len(rows), "orders": rows[0]["orders"] if rows else 0, "share_median": st.median(shares), "share_min": min(shares), "share_max": max(shares),
            "gap_mean": st.mean(r["gap_mean"] for r in rows), "gap_median": st.median(r["gap_median"] for r in rows)}


def method_gaps(m: int) -> dict:
    rows = [r for r in load_bands()["methods"] if r["m"] == m]
    out = {}
    for key in ("ins1", "ins_mean10", "ins10", "nn", "rand1", "rand100"):
        v = [gap_percent(r[key], r["opt"]) for r in rows]
        out[key] = {"mean": st.mean(v), "median": st.median(v), "max": max(v), "optimal": sum(1 for x in v if x < 1e-6), "count": len(v)}
    return out


def dominance_stats() -> dict:
    b = load_bands()
    ds, dr = b["dominance_stops"], b["dominance_requests"]
    return {"stops_ok": sum(1 for r in ds if abs(r["best"] - r["opt"]) < 1e-9), "stops_n": len(ds), "stops_perms": ds[0]["perms"] if ds else 0,
            "stops_feasible": sum(r["feasible"] for r in ds), "requests_ok": sum(1 for r in dr if abs(r["best"] - r["opt"]) < 1e-9), "requests_n": len(dr)}


def position_stats(k: int) -> dict:
    r = next(x for x in load_bands()["positions"] if x["k"] == k)
    return {"pairs": r["pairs"] / r["routes"], "capacity_ok": r["capacity_ok"] / r["routes"], "share": 100.0 * r["capacity_ok"] / r["pairs"], "stops": r["stops"]}


# ----------------------------------------------------------------------------------------------------------------------------------- Live-Rechnungen

@dataclass(frozen=True, eq=False)
class Levels:
    """Zufällige Folge auf beiden Ebenen: Haltefolge und Auftragsfolge derselben Instanz."""
    stop_seq: tuple
    stop_cost: float
    stop_blocks: object
    order: tuple
    order_cost: float
    order_blocks: object
    sample_n: int
    sample_feasible: int


def levels(inst: M.Instance, stop_seed: int, order_seed: int, sample_n: int = 1000) -> Levels:
    seq = SP.random_stop_sequence(inst, random.Random(stop_seed))
    sc, sb = SP.split_stops(inst, seq)
    order = SP.random_request_order(inst, random.Random(order_seed))
    oc, ob = SP.split_requests(inst, order)
    rng = random.Random(stop_seed * 7919 + 13)
    feasible = sum(1 for _ in range(sample_n) if SP.split_stops(inst, SP.random_stop_sequence(inst, rng))[0] < INF)
    return Levels(tuple(seq), sc, sb, tuple(order), oc, ob, sample_n, feasible)


@dataclass(frozen=True, eq=False)
class Enumeration:
    opt: float
    costs: tuple           # Kosten des Splits jeder Auftragsfolge (m! Stück, in itertools-Reihenfolge)
    optimal: int

    @property
    def share(self) -> float:
        return 100.0 * self.optimal / len(self.costs)

    @property
    def gap_mean(self) -> float:
        return 100.0 * (st.mean(self.costs) / self.opt - 1)

    @property
    def gap_median(self) -> float:
        return 100.0 * (st.median(self.costs) / self.opt - 1)

    @property
    def gap_max(self) -> float:
        return 100.0 * (max(self.costs) / self.opt - 1)


def enumerate_orders(inst: M.Instance) -> Enumeration:
    if inst.m > C.ENUM_MAX:
        raise ValueError(f"Aufzählung nur bis {C.ENUM_MAX} Aufträge")
    wl = M.limited_costs(inst)
    opt = M.solve(inst).cost
    costs = tuple(SP.split_requests(inst, p, wl)[0] for p in itertools.permutations(range(inst.m)))
    return Enumeration(opt, costs, sum(1 for c in costs if abs(c - opt) < 1e-9))


@dataclass(frozen=True, eq=False)
class Comparison:
    opt: float
    results: dict          # Schlüssel -> (Kosten, Routen als Haltefolgen)
    k_insert: int
    k_orders: int
    insertion_lengths: tuple


def compare(inst: M.Instance, k_insert: int, k_orders: int, seed: int) -> Comparison:
    """Alle Verfahren auf der Instanz mit festem Seed: Einfügen (erste Reihenfolge und bestes von k), nächster Nachbar + Split, erste und beste von k Auftragsfolgen + Split, Optimum."""
    sol = M.solve(inst)
    rng = random.Random(seed)
    best_len, lengths, best_routes = H.best_insertion(inst, k_insert, rng)
    first_routes = H.insertion_heuristic(inst, SP.random_request_order(inst, random.Random(seed + 1)))
    wl = M.limited_costs(inst)
    nn_cost, nn_blocks = SP.split_requests(inst, H.nn_order(inst), wl)
    rng2 = random.Random(seed + 2)
    first_order = SP.random_request_order(inst, rng2)
    f_cost, f_blocks = SP.split_requests(inst, first_order, wl)
    b_cost, b_blocks, b_order = H.best_orders(inst, k_orders, random.Random(seed + 3))
    res = {"opt": (sol.cost, list(sol.routes)),
           "ins1": (M.plan_length(inst, first_routes), first_routes),
           "insk": (best_len, best_routes),
           "nn": (nn_cost, H.blocks_to_routes(inst, nn_blocks)),
           "rand1": (f_cost, H.blocks_to_routes(inst, f_blocks)),
           "randk": (b_cost, H.blocks_to_routes(inst, b_blocks))}
    return Comparison(sol.cost, res, k_insert, k_orders, tuple(lengths))


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_levels(inst: M.Instance, lv: Levels) -> tuple[str, str]:
    """Experiment 1: dieselbe Instanz, eine Zufallsfolge von Halten gegen eine von Aufträgen."""
    sample = f"Von {lv.sample_n} zufälligen Haltefolgen dieser Instanz lassen sich {lv.sample_feasible} ({pct(100.0 * lv.sample_feasible / lv.sample_n, 2)}) in zulässige Routen zerlegen; jede Auftragsfolge lässt sich zerlegen."
    opt = M.solve(inst).cost
    if lv.stop_blocks is None:
        text = (f"Die Haltefolge hat keine zulässige Zerlegung (Abholen und Liefern liegen in keinem Block beisammen, oder die Last oder die Streckengrenze wird verletzt). Die Auftragsfolge {requests_text(lv.order)} "
                f"zerlegt sich in {routes_word(len(lv.order_blocks))} {blocks_text(lv.order_blocks)} mit Länge {de(lv.order_cost)} ({signed_pct(gap_percent(lv.order_cost, opt))} gegen das Optimum {de(opt)}). {sample}")
        return "warning", text
    text = (f"Die Haltefolge zerlegt sich in {routes_word(len(lv.stop_blocks))} mit Länge {de(lv.stop_cost)} ({signed_pct(gap_percent(lv.stop_cost, opt))} gegen das Optimum {de(opt)}); "
            f"die Auftragsfolge {requests_text(lv.order)} in {routes_word(len(lv.order_blocks))} mit Länge {de(lv.order_cost)} ({signed_pct(gap_percent(lv.order_cost, opt))}). {sample}")
    return "info", text


def verdict_order(inst: M.Instance, order, cost: float, blocks) -> tuple[str, str]:
    """Experiment 2: eine Auftragsfolge von Hand."""
    opt = M.solve(inst).cost
    gap = gap_percent(cost, opt)
    head = f"Die Folge {requests_text(order)} zerlegt sich in {routes_word(len(blocks))} {blocks_text(blocks)} mit Länge {de(cost)}; das Optimum ist {de(opt)}"
    if gap <= C.TOL:
        return "success", head + ": diese Folge liefert es."
    return "info", head + f" ({signed_pct(gap)} Lücke): diese Folge liefert es nicht."


def verdict_rarity(inst: M.Instance, en: Enumeration) -> tuple[str, str]:
    """Experiment 3: alle Auftragsfolgen einer Instanz."""
    n = len(en.costs)
    return "info", (f"Von {n} Auftragsfolgen liefern {en.optimal} ({pct(en.share)}) das Optimum {de(en.opt)}; eine zufällige Folge liegt im Mittel {pct(en.gap_mean)} darüber (Median {pct(en.gap_median)}, schlechteste {pct(en.gap_max)}). "
                    f"Jede dieser Folgen ist zulässig.")


def verdict_methods(inst: M.Instance, cmp_: Comparison) -> tuple[str, str]:
    """Experiment 4: Verfahren auf einer Instanz."""
    r = cmp_.results
    gaps = {k: gap_percent(v[0], cmp_.opt) for k, v in r.items()}
    best_heur = min((k for k in r if k != "opt"), key=lambda k: (r[k][0], k))
    text = (f"Optimum {de(cmp_.opt)}. Einfügen mit einer Reihenfolge {signed_pct(gaps['ins1'])}, bestes von {cmp_.k_insert} Reihenfolgen {signed_pct(gaps['insk'])}; nächster Nachbar + Split {signed_pct(gaps['nn'])}; "
            f"eine Auftragsfolge + Split {signed_pct(gaps['rand1'])}, bestes von {cmp_.k_orders} Folgen {signed_pct(gaps['randk'])}. Das beste der Verfahren: {METHOD_LABEL[best_heur]}.")
    kind = "success" if gaps[best_heur] <= C.TOL else "info"
    return kind, text


METHOD_LABEL = {"opt": "Optimum (exakt)", "ins1": "Einfügen, eine Zufallsreihenfolge", "insk": "Einfügen, bestes von k Reihenfolgen", "nn": "Nächster Nachbar auf Aufträgen + Split",
                "rand1": "Eine zufällige Auftragsfolge + Split", "randk": "Bestes von k Auftragsfolgen + Split"}


def verdict_positions(route, request: int, options) -> tuple[str, str]:
    """Experiment 5: Einfügepositionen eines Auftrags in eine Route."""
    total = len(options)
    cap = sum(1 for o in options if o[2])
    ok = sum(1 for o in options if o[3])
    return "info", (f"Eine Route mit {len(route)} Halten hat {total} Positionspaare (Abholen an Position a, Liefern an Position b ≥ a) für Auftrag {request + 1}; {cap} halten die Last, {ok} halten auch die Streckengrenze ein. "
                    f"Ohne die Paarbedingung gäbe es {len(route) + 1} Positionen je Halt.")


def verdict_bands(m: int) -> tuple[str, str]:
    """Bänder der Verfahren (m = 6, 7, 8)."""
    g = method_gaps(m)
    n = g["ins1"]["count"]
    return "info", (f"{instances_word(n)} mit {m} Aufträgen: Einfügen einmal {pct(g['ins1']['mean'])} über dem Optimum, bestes von 10 Reihenfolgen {pct(g['ins10']['mean'])} (Optimum in {g['ins10']['optimal']} von {n}); "
                    f"nächster Nachbar + Split {pct(g['nn']['mean'])}; bestes von 100 Auftragsfolgen + Split {pct(g['rand100']['mean'])} (Optimum in {g['rand100']['optimal']} von {n}). Ein Lauf je Instanz, kleine Instanzen mit exaktem Optimum.")


# ----------------------------------------------------------------------------------------------------------------------------------- Weitere Fälle und Kernverdikt

def insertion_case(inst: M.Instance, route_index: int, request_choice: int):
    """Fall für Experiment 5: (Route, Auftrag, Optionen). Basis ist die Route `route_index` des Optimums; `request_choice` zählt die Aufträge, die nicht in dieser Route liegen. Besteht das Optimum nur aus einer Route,
    wird deren letzter Auftrag herausgenommen und wieder eingefügt."""
    sol = M.solve(inst)
    routes = [list(r) for r in sol.routes]
    base = routes[route_index % len(routes)]
    outside = sorted({M.request_of(s) for r in routes for s in r} - {M.request_of(s) for s in base})
    if not outside:
        last = M.request_of(base[-1])
        base = [s for s in base if M.request_of(s) != last]
        outside = [last]
    request = outside[request_choice % len(outside)]
    return base, request, H.insertion_options(inst, base, request), outside


def order_with_rest(selected, m: int) -> list[int]:
    """Die gewählten Aufträge in der Reihenfolge der Wahl, dahinter die übrigen in Nummernfolge (Nummern ab 0)."""
    chosen = list(dict.fromkeys(selected))
    return chosen + [i for i in range(m) if i not in chosen]


def verdict_core() -> tuple[str, str]:
    """Die Kernfrage: trägt das Rückgrat Riesentour + Split bei Paaren? Zahlen aus den Bändern."""
    d = dominance_stats()
    f = {m: feas_stats(m) for m in (4, 6, 8)}
    e = {m: enum_stats(m) for m in (5, 6, 7)}
    g8 = method_gaps(8)
    return "info", (f"Die Dominanz gilt auf beiden Ebenen (Haltefolgen: {d['stops_ok']} von {d['stops_n']} Instanzen, Auftragsfolgen: {d['requests_ok']} von {d['requests_n']}). Auf der Halteebene ist aber fast jede Folge unzulässig: "
                    f"zerlegbar sind {pct(f[4]['p_limit'], 2)} der zufälligen Haltefolgen bei 4 Aufträgen und {pct(f[6]['p_limit'], 2)} bei 6. Auf der Auftragsebene ist jede Folge zulässig, und das Optimum ist selten wie in Stück 1 "
                    f"({pct(e[5]['share_median'])} der Folgen bei 5, {pct(e[7]['share_median'])} bei 7 Aufträgen). Bei 8 Aufträgen liegt das beste von 100 Auftragsfolgen + Split {pct(g8['rand100']['mean'])} über dem Optimum, "
                    f"Einfügen in einer Reihenfolge {pct(g8['ins1']['mean'])}.")


def default_insertion_choice(inst: M.Instance, route_index: int | None = None) -> tuple[int, int]:
    """Voreinstellung für Experiment 5: (Route, Auftrag) mit den meisten ganz zulässigen Positionspaaren (danach den meisten kapazitätszulässigen; Gleichstand: der erste). Mit `route_index` nur über diese Route."""
    n_routes = len(M.solve(inst).routes)
    best, choice = (-1, -1), (0, 0)
    for r in ([route_index] if route_index is not None else range(n_routes)):
        _, _, _, outside = insertion_case(inst, r, 0)
        for q in range(len(outside)):
            _, _, options, _ = insertion_case(inst, r, q)
            score = (sum(1 for o in options if o[3]), sum(1 for o in options if o[2]))
            if score > best:
                best, choice = score, (r, q)
    return choice
