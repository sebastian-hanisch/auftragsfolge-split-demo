"""Split auf zwei Ebenen: Folge von Halten und Folge von Aufträgen (Stück 10).

Haltefolge: eine Permutation aller 2m Halte; Split zerlegt sie in zusammenhängende Blöcke, jeder Block muss selbst eine zulässige Route sein (beide Halte jedes Auftrags im Block, Abholen vor Liefern,
Last höchstens Q, Länge höchstens Lmax). Auftragsfolge: eine Permutation der m Aufträge; Split zerlegt sie in zusammenhängende Blöcke, Blockpreis = kürzeste Route der Auftragsmenge des Blocks
(exakt aus der Tabelle), unendlich, wenn sie länger als Lmax ist. Jede Auftragsfolge ist zulässig, weil jeder Auftrag allein eine Route ist."""

import math
import random

import afs_constants as C
import afs_model as M

INF = math.inf


def block_cost(inst: M.Instance, stops, check_limit: bool = True):
    """Länge der Route aus diesen Halten in dieser Reihenfolge, wenn sie zulässig ist, sonst None."""
    if not stops or not M.route_is_valid(inst, stops, check_limit):
        return None
    return M.route_length(inst, stops)


def split_stops(inst: M.Instance, seq, check_limit: bool = True):
    """Beste Zerlegung einer Haltefolge: (Kosten, Blöcke als Tupel von Halten) oder (inf, None), wenn es keine zulässige Zerlegung gibt."""
    L = len(seq)
    best = [INF] * (L + 1)
    pred = [-1] * (L + 1)
    best[0] = 0.0
    for i in range(L):
        if best[i] == INF:
            continue
        for j in range(i + 2, L + 1, 2):
            c = block_cost(inst, seq[i:j], check_limit)
            if c is not None and best[i] + c < best[j] - 1e-12:
                best[j] = best[i] + c
                pred[j] = i
    if best[L] == INF:
        return INF, None
    blocks, node = [], L
    while node > 0:
        blocks.append(tuple(seq[pred[node]:node]))
        node = pred[node]
    blocks.reverse()
    return best[L], tuple(blocks)


def split_requests(inst: M.Instance, order, wl=None):
    """Beste Zerlegung einer Auftragsfolge: (Kosten, Blöcke als Tupel von Aufträgen). `wl`: Blockpreise mit Streckengrenze (Voreinstellung: aus der Instanz)."""
    m = inst.m
    wl = wl if wl is not None else M.limited_costs(inst)
    best = [INF] * (m + 1)
    pred = [-1] * (m + 1)
    best[0] = 0.0
    for i in range(m):
        if best[i] == INF:
            continue
        mask = 0
        for j in range(i, m):
            mask |= 1 << order[j]
            c = wl[mask]
            if c < INF and best[i] + c < best[j + 1] - 1e-12:
                best[j + 1] = best[i] + c
                pred[j + 1] = i
    if best[m] == INF:
        return INF, None
    blocks, node = [], m
    while node > 0:
        blocks.append(tuple(order[pred[node]:node]))
        node = pred[node]
    blocks.reverse()
    return best[m], tuple(blocks)


def random_stop_sequence(inst: M.Instance, rng: random.Random) -> list[int]:
    seq = list(range(1, 2 * inst.m + 1))
    rng.shuffle(seq)
    return seq


def random_request_order(inst: M.Instance, rng: random.Random) -> list[int]:
    return rng.sample(range(inst.m), inst.m)


def stop_text(stop: int) -> str:
    """Halt als Text: A1 = Abholen von Auftrag 1, L1 = Liefern von Auftrag 1."""
    return ("A" if stop % 2 == 1 else "L") + str(M.request_of(stop) + 1)


def stops_text(stops) -> str:
    return " ".join(stop_text(s) for s in stops)
