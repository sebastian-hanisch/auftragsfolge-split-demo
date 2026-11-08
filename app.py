"""Abholen und Liefern: Riesentour über Aufträge - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 10 der Reihe „Tourenbildung“: Trägt das Rückgrat Riesentour + Split, wenn Aufträge aus einem Abholpunkt und einem Lieferpunkt bestehen? Die Demo stellt die Folge einzelner Halte (fast nie zerlegbar) der Folge von Aufträgen
(immer zerlegbar, Blockpreis = beste Route der Menge) gegenüber, zählt die Folgen auf, vergleicht Einfügen, nächsten Nachbarn und Folgen mit Split mit dem exakten Optimum und zeigt die Einfügepositionen.

Lauffähig mit: streamlit run app.py
"""

import math

import streamlit as st

import afs_constants as C
import afs_heuristics as H
import afs_model as M
import afs_split as SP
from afs_evaluation import (
    Settings,
    blocks_text,
    build_instance,
    compare,
    de,
    dominance_stats,
    enum_stats,
    enumerate_orders,
    feas_stats,
    gap_percent,
    default_insertion_choice,
    insertion_case,
    instances_word,
    levels,
    method_gaps,
    order_with_rest,
    pct,
    position_stats,
    requests_text,
    routes_word,
    signed_pct,
    verdict_bands,
    verdict_core,
    verdict_levels,
    verdict_methods,
    verdict_order,
    verdict_positions,
    verdict_rarity,
)
from afs_layout import dunkles_design, kopf_css
from afs_pdf_export import build_pdf
from afs_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from afs_visualization import build_gap_histogram, build_map, build_positions

st.set_page_config(page_title="Abholen und Liefern – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _solve(settings):
    sol = M.solve(build_instance(settings))
    return sol


@st.cache_data(show_spinner=False)
def _levels(settings, stop_seed, order_seed):
    return levels(build_instance(settings), stop_seed, order_seed)


@st.cache_data(show_spinner=False)
def _enum(settings):
    return enumerate_orders(build_instance(settings))


@st.cache_data(show_spinner=False)
def _compare(settings, k_insert, k_orders, seed):
    return compare(build_instance(settings), k_insert, k_orders, seed)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in afs_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📦 Abholen und Liefern: Riesentour über Aufträge")
st.markdown(
    """
**Trägt das Rückgrat bei Paaren?** Ein Auftrag besteht aus einem **Abholpunkt** und einem **Lieferpunkt**, beide müssen in derselben Route liegen, Abholen vor Liefern, und die Route darf eine **Streckengrenze** nicht überschreiten.
Die **Riesentour** (Stücke 1 bis 3) ist eine Reihenfolge, der **Split** zerlegt sie optimal in Routen. Hier gibt es zwei Arten von Riesentouren: eine Folge aller **Halte** und eine Folge der **Aufträge**. Die Demo zeigt, warum
die erste fast nie zerlegbar ist und die zweite immer, und was das für Einfügen und Suchen bedeutet.

Weiter unten: **🔬 Zwei Ebenen**, **🔬 Eine Auftragsfolge von Hand**, **🔬 Die Seltenheit**, **🔬 Verfahren im Vergleich**, **🔬 Einfügepositionen**, **🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme**
und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So arbeitet die Demo", expanded=True):
    st.markdown(
        """
1. **Modell:** Ein Depot, m Aufträge mit Abholpunkt (A1, A2, …), Lieferpunkt (L1, L2, …) und Last, ein Fahrzeug der Kapazität Q, eine **Streckengrenze** je Route. Ziel: kürzeste Gesamtlänge. Ohne die Streckengrenze wäre eine einzige Route durch alle Aufträge optimal.
2. **Haltefolge:** eine Reihenfolge aller 2m Halte; der Split schneidet sie in Blöcke, jeder Block muss selbst eine zulässige Route sein (beide Halte jedes Auftrags im Block, Abholen vor Liefern, Last, Streckengrenze).
3. **Auftragsfolge:** eine Reihenfolge der m Aufträge; der Split schneidet sie in Blöcke von Aufträgen, ein Block kostet die **kürzeste Route seiner Auftragsmenge** (wie die Rundreise je Cluster in Stück 6). Jeder Auftrag allein ist eine Route, jede Folge ist also zerlegbar.
4. **Exaktes Optimum:** ein DP über (Status je Auftrag, letzter Halt) gibt für jede Auftragsmenge die kürzeste Route, eine Partitions-DP darüber das Optimum (bis 8 Aufträge).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    family = st.selectbox("Art der Instanz", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Handinstanz“: vier Aufträge auf den vier Achsen um das Depot (Kapazität 3, Streckengrenze 22). „Zufällig“: Koordinaten 0 bis 100, Last 1 bis 3.")
    hand = int(family) == C.HAND_FAMILY
    if hand:
        st.caption("Bei der Handinstanz gelten Aufträge, Depot, Kapazität, Streckengrenze und Seed nicht; die Instanz ist fest.")
    m = st.slider("Aufträge m", *bounds("m_slider"), key="m_slider", help=f"Live gerechnet wird bis {C.EXACT_LIVE_MAX} Aufträge (exakter DP über 3^m Zustände, alle m! Auftragsfolgen); die Bänder gehen bis 8.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    cap = st.slider("Kapazität Q", *bounds("cap_slider"), key="cap_slider", help="Größte Last im Fahrzeug; die Last der Aufträge ist 1 bis 3.")
    limit = st.slider("Streckengrenze (% der kürzesten Gesamtroute)", *bounds("limit_slider"), step=C.LIMIT_STEP, key="limit_slider",
                      help="Grenze je Route in Prozent der kürzesten Route über alle Aufträge, mindestens die längste Einzelroute. Bei 100 % ist eine Route durch alle Aufträge zulässig: dann ist sie optimal.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed legt die Instanz fest (außer bei der Handinstanz).")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"family_select": int(family), "m_slider": int(m), "depot_select": int(depot), "cap_slider": int(cap), "limit_slider": int(limit), "seed_input": int(seed)})

settings = Settings(int(family), int(m), int(depot), int(cap), int(limit), int(seed))
inst = build_instance(settings)
sol = _solve(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: das exakte Optimum")
c1, c2, c3 = st.columns(3)
c1.metric("Kürzeste Gesamtlänge", de(sol.cost))
c2.metric("Routen im Optimum", str(len(sol.routes)))
c3.metric("Streckengrenze je Route", de(inst.Lmax, 1) if math.isfinite(inst.Lmax) else "keine")
st.caption(f"{inst.m} Aufträge, Kapazität {inst.Q}, Last {', '.join(str(x) for x in inst.q)}. Blöcke des Optimums (Auftragsmengen): "
           + " ‖ ".join("(" + " ".join(str(i + 1) for i in M.mask_requests(b)) + ")" for b in sol.blocks) + ".")
st.plotly_chart(build_map(inst, sol.routes), width="stretch", key="map_opt")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, inst, sol), file_name="abholen-und-liefern.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Trägt das Rückgrat Riesentour + Split bei Paaren?")
kind, text = verdict_core()
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Zwei Ebenen: Halte oder Aufträge")
st.caption("Dieselbe Instanz, zwei zufällige Folgen: links alle 2m Halte in zufälliger Reihenfolge, rechts die m Aufträge. Der Split sucht die beste Zerlegung in zulässige Blöcke. Darunter, wie viele zufällige Haltefolgen dieser Instanz sich überhaupt zerlegen lassen.")
e1, e2 = st.columns(2)
with e1:
    stop_seed = int(st.number_input("Seed der Haltefolge", 0, 10 ** 6, 1, key="stop_seed", step=1))
with e2:
    order_seed = int(st.number_input("Seed der Auftragsfolge", 0, 10 ** 6, 1, key="order_seed", step=1))
lv = _levels(settings, stop_seed, order_seed)
x1, x2 = st.columns(2)
with x1:
    st.markdown(f"**Haltefolge:** {SP.stops_text(lv.stop_seq)}")
    if lv.stop_blocks is None:
        st.error("Keine zulässige Zerlegung: kein Schnitt der Folge ergibt nur zulässige Routen.")
    else:
        st.markdown(f"Split: **{de(lv.stop_cost)}** ({routes_word(len(lv.stop_blocks))}): " + " ‖ ".join("(" + SP.stops_text(b) + ")" for b in lv.stop_blocks))
        st.plotly_chart(build_map(inst, [list(b) for b in lv.stop_blocks], legend=False), width="stretch", key="map_stops")
with x2:
    st.markdown(f"**Auftragsfolge:** {requests_text(lv.order)}")
    st.markdown(f"Split: **{de(lv.order_cost)}** ({routes_word(len(lv.order_blocks))}): {blocks_text(lv.order_blocks)}")
    st.plotly_chart(build_map(inst, H.blocks_to_routes(inst, lv.order_blocks), legend=False), width="stretch", key="map_orders")
kind, text = verdict_levels(inst, lv)
getattr(st, kind)(text)
rows = ["| Aufträge m | zerlegbare Haltefolgen (mit Streckengrenze) | ohne Streckengrenze (nur Kapazität und Abholen vor Liefern) |", "|---|---|---|"]
for mm in C.BAND_FEAS_SIZES:
    f = feas_stats(mm)
    rows.append(f"| {mm} | {pct(f['p_limit'], 2)} ({f['limit']} von {f['seqs']}) | {pct(f['p_nolimit'], 2)} ({f['nolimit']} von {f['seqs']}) |")
st.markdown("\n".join(rows))
st.caption(f"Bänder: {instances_word(feas_stats(C.BAND_FEAS_SIZES[0])['instances'])} je Größe mit je {C.BAND_RANDOM_SEQS} zufälligen Haltefolgen, Kapazität {C.BAND_Q}, Streckengrenze {C.BAND_LIMIT} % (vorberechnet, generate_precomputed.py).")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Eine Auftragsfolge von Hand")
st.caption("Wählen Sie die Aufträge in der gewünschten Reihenfolge aus; was Sie nicht wählen, wird in Nummernfolge angehängt. Der Split schneidet die Folge in Blöcke, jeder Block bekommt die kürzeste Route seiner Auftragsmenge.")
selected = st.multiselect("Aufträge in Reihenfolge", list(range(1, inst.m + 1)), key=f"order_sel_{inst.m}_{settings.family}", format_func=lambda i: f"Auftrag {i}")
order = order_with_rest([i - 1 for i in selected], inst.m)
wl = M.limited_costs(inst)
ocost, oblocks = SP.split_requests(inst, order, wl)
st.markdown(f"**Folge:** {requests_text(order)}  \nSplit **{de(ocost)}** ({routes_word(len(oblocks))}): {blocks_text(oblocks)}")
st.plotly_chart(build_map(inst, H.blocks_to_routes(inst, oblocks), legend=False), width="stretch", key="map_hand_order")
kind, text = verdict_order(inst, order, ocost, oblocks)
getattr(st, kind)(text)
opt_order = [i for b in sol.blocks for i in M.mask_requests(b)]
st.caption(f"Eine Folge, deren Split das Optimum liefert: {requests_text(opt_order)} (die Blöcke des Optimums nacheinander).")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Seltenheit")
st.caption("Alle m! Auftragsfolgen dieser Instanz: wie viele liefern das Optimum, wie weit liegt eine zufällige Folge darüber? Wie in Stück 1 gibt es viele Folgen und wenige beste. Darunter die Bänder und die Dominanzprüfung.")
if inst.m <= C.ENUM_MAX:
    en = _enum(settings)
    st.plotly_chart(build_gap_histogram(en.costs, en.opt), width="stretch", key="gap_hist")
    kind, text = verdict_rarity(inst, en)
    getattr(st, kind)(text)
else:
    st.info(f"Die Aufzählung gilt bis {C.ENUM_MAX} Aufträge.")
rows = ["| Aufträge m | Folgen | optimale Folgen: Median | kleinster / größter Anteil | Lücke einer zufälligen Folge: Mittel | Median |", "|---|---|---|---|---|---|"]
for mm in C.BAND_ENUM_SIZES:
    s_ = enum_stats(mm)
    rows.append(f"| {mm} | {s_['orders']} | {pct(s_['share_median'])} | {pct(s_['share_min'])} / {pct(s_['share_max'])} | {pct(s_['gap_mean'])} | {pct(s_['gap_median'])} |")
st.markdown("\n".join(rows))
d = dominance_stats()
st.caption(f"Bänder: {instances_word(enum_stats(4)['instances'])} je Größe. **Dominanz** (das Minimum des Splits über alle Folgen ist das exakte Optimum): alle {d['stops_perms']} Haltefolgen bei 4 Aufträgen in {d['stops_ok']} von {d['stops_n']} Instanzen "
           f"(davon nur {d['stops_feasible']} Folgen insgesamt zerlegbar), alle Auftragsfolgen bei 5 Aufträgen in {d['requests_ok']} von {d['requests_n']} Instanzen.")

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Verfahren im Vergleich")
st.caption("Einfügen (Aufträge nacheinander an der billigsten zulässigen Stelle, sonst neue Route), nächster Nachbar auf Aufträgen + Split, zufällige Auftragsfolgen + Split, jeweils gegen das exakte Optimum. Zufallsverfahren mit festem Seed.")
if inst.m > C.EXACT_LIVE_MAX:
    st.info(f"Live gerechnet wird bis {C.EXACT_LIVE_MAX} Aufträge.")
else:
    k1, k2, k3 = st.columns(3)
    with k1:
        k_ins = int(st.slider("Einfügeläufe (bestes von k)", *C.LIVE_K_INSERT[:2], C.LIVE_K_INSERT[2], key="ins_k"))
    with k2:
        k_ord = int(st.slider("Auftragsfolgen (bestes von k)", *C.LIVE_K_ORDERS[:2], C.LIVE_K_ORDERS[2], key="ord_k"))
    with k3:
        cmp_seed = int(st.number_input("Seed der Zufallsverfahren", 0, 10 ** 6, 0, key="cmp_seed", step=1))
    cmp_ = _compare(settings, k_ins, k_ord, cmp_seed)
    labels = {"opt": "Optimum (exakt)", "ins1": "Einfügen, eine Zufallsreihenfolge", "insk": f"Einfügen, bestes von {k_ins} Reihenfolgen", "nn": "Nächster Nachbar auf Aufträgen + Split",
              "rand1": "Eine zufällige Auftragsfolge + Split", "randk": f"Bestes von {k_ord} Auftragsfolgen + Split"}
    rows = ["| Verfahren | Gesamtlänge | Lücke zum Optimum | Routen |", "|---|---|---|---|"]
    for key, (cost, routes) in cmp_.results.items():
        rows.append(f"| {labels[key]} | {de(cost)} | {signed_pct(gap_percent(cost, cmp_.opt))} | {len(routes)} |")
    st.markdown("\n".join(rows))
    show = st.selectbox("Plan anzeigen", list(labels), key="show_method", format_func=lambda k: labels[k])
    st.plotly_chart(build_map(inst, [list(r) for r in cmp_.results[show][1]]), width="stretch", key="map_method")
    kind, text = verdict_methods(inst, cmp_)
    getattr(st, kind)(text)
band_m = int(st.radio("Aufträge m (Bänder)", list(C.BAND_METHOD_SIZES), horizontal=True, key="band_m"))
g = method_gaps(band_m)
rows = ["| Verfahren | Lücke: Mittel | Median | Maximum | Optimum in |", "|---|---|---|---|---|"]
for key, label in (("ins1", "Einfügen, eine Reihenfolge"), ("ins_mean10", "Einfügen, Mittel von 10 Reihenfolgen"), ("ins10", "Einfügen, bestes von 10"), ("nn", "Nächster Nachbar + Split"),
                   ("rand1", "Eine Auftragsfolge + Split"), ("rand100", "Bestes von 100 Auftragsfolgen + Split")):
    v = g[key]
    rows.append(f"| {label} | {pct(v['mean'])} | {pct(v['median'])} | {pct(v['max'])} | {v['optimal']} von {v['count']} |")
st.markdown("\n".join(rows))
kind, text = verdict_bands(band_m)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Einfügepositionen")
st.caption("Ein Auftrag wird in eine Route des Optimums eingefügt: Abholen an Position a, Liefern an Position b ≥ a. Die Heatmap zeigt jedes Positionspaar (grün: Last und Streckengrenze gehalten, gelb: nur die Last, grau: unzulässig) mit der Mehrlänge.")
n_routes = len(sol.routes)
p1, p2 = st.columns(2)
with p1:
    route_idx = int(st.selectbox("Route des Optimums", list(range(n_routes)), index=default_insertion_choice(inst)[0], key=f"pos_route_{inst.m}_{settings.family}", format_func=lambda i: f"Route {i + 1}"))
base, _, _, outside = insertion_case(inst, route_idx, 0)
with p2:
    req_idx = int(st.selectbox("Einzufügender Auftrag", list(range(len(outside))), index=default_insertion_choice(inst, route_idx)[1], key=f"pos_req_{inst.m}_{settings.family}_{route_idx}", format_func=lambda i: f"Auftrag {outside[i] + 1}"))
base, request, options, outside = insertion_case(inst, route_idx, req_idx)
st.markdown(f"**Route:** {SP.stops_text(base)}  \n**Einzufügen:** A{request + 1} und L{request + 1}")
st.plotly_chart(build_positions(options, len(base)), width="stretch", key="pos_heat")
kind, text = verdict_positions(base, request, options)
getattr(st, kind)(text)
rows = ["| Aufträge in der Route k | Halte | Positionspaare (a ≤ b) | davon kapazitätszulässig | Anteil |", "|---|---|---|---|---|"]
for k in C.BAND_POSITION_SIZES:
    s_ = position_stats(k)
    rows.append(f"| {k} | {s_['stops']} | {de(s_['pairs'], 1)} | {de(s_['capacity_ok'], 1)} | {pct(s_['share'], 0)} |")
st.markdown("\n".join(rows))
st.caption(f"Bänder: {C.BAND_POSITION_ROUTES} zufällig gebaute kapazitätszulässige Routen je k (Zufallsablauf unter Kapazität {C.BAND_Q}, nicht gleichverteilt über alle Routen, Streckengrenze nicht geprüft), Mittel je Route. Die Zahl der Positionspaare wächst quadratisch mit der Zahl der Halte; ohne die Paarbedingung gäbe es 2k + 1 Positionen je Halt.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Streckengrenze bindet** | Ohne sie (oder mit 100 %) ist eine Route durch alle Aufträge optimal: jede Auftragsfolge ist dann optimal, die Frage der Zerlegung entfällt | Zeitfenster (Stücke 8 und 9) |
| **Blockpreis exakt** | Nur bei kleinen Mengen (hier bis 8 Aufträge); bei großen Instanzen braucht die Route je Block eine Heuristik, die Dominanz gilt dann nicht mehr für den Preis | Rundreise je Cluster (Stück 6) |
| **Kleine Zufallsinstanzen** | Die Zahlen gelten für diese Instanzen, nicht für Li-Lim-Benchmarks oder echte Auftragsdaten | Benchmarksätze (nicht geladen) |
| **Einfache Verfahren, ein Lauf** | Einfügen ohne Neuordnen, Zufallsfolgen mit festem Seed; eine genetische Suche über Auftragsfolgen ist nicht gemessen | Stück 11 mit Auftragsfolgen (nicht gebaut) |
| **Keine Fenster, keine Fahrtzeit je Auftrag** | Dial-a-Ride mit Wartezeit und Fahrtzeitgrenzen je Person ändert den Blockpreis | Fachliteratur (Cordeau, Laporte) |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Depot $0$, Aufträge $i = 1, \dots, m$ mit Abholpunkt $p_i$, Lieferpunkt $d_i$ und Last $q_i$, Kapazität $Q$, Streckengrenze $L$. Eine Route ist eine Folge von Halten, die jeden Auftrag ganz enthält oder gar nicht, mit $p_i$ vor $d_i$,
Last $\sum_{i \text{ unterwegs}} q_i \le Q$ an jeder Stelle und Länge $\le L$.

**Blockpreis.** Für eine Auftragsmenge $S$ sei $w(S)$ die Länge der kürzesten zulässigen Route durch genau diese Aufträge (kapazitätsgerecht, unendlich, wenn sie länger als $L$ ist). Berechnung: DP über den Zustand
$(s, \ell)$, $s \in \{0, 1, 2\}^m$ (offen, abgeholt, geliefert), $\ell$ letzter Halt, $3^m (2m + 1)$ Zustände.

**Optimum.** $f(\emptyset) = 0$, $f(S) = \min_{T \subseteq S,\, T \ni \min S} \{ f(S \setminus T) + w(T) \}$.

**Split auf Aufträgen.** Für eine Folge $\sigma$ der Aufträge ist $\operatorname{Split}(\sigma)$ der kürzeste Weg im Hilfsgraphen mit den Bögen $(i, j)$ und dem Gewicht $w(\{\sigma_{i+1}, \dots, \sigma_j\})$ (Stücke 1 und 6).

**Dominanz.** Aus jeder zulässigen Lösung entsteht durch Aneinanderhängen der Routen (Aufträge in der Reihenfolge ihrer ersten Halte) eine Folge, deren Split sie oder eine nicht längere liefert: $\min_\sigma \operatorname{Split}(\sigma) = f(\{1, \dots, m\})$.
Für Haltefolgen gilt dasselbe mit Blöcken zusammenhängender Halte, aber ein zufälliger Block ist fast nie eine zulässige Route.

**Literatur.** Riesentour und Split: Beasley (1983), Prins (2004); Abholen und Liefern: Cordeau und Laporte (2007), Ropke und Pisinger (2006); beide nur als Titel oder Abstract gesehen, die Demo übernimmt keine Zahl daraus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
