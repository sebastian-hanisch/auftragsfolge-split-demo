"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import afs_constants as C
import afs_model as M
import afs_split as SP


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst: M.Instance, routes, legend: bool = True):
    """Karte: Depot als Quadrat, Abholpunkte als Dreiecke nach oben (A1, A2, …), Lieferpunkte als Dreiecke nach unten (L1, L2, …), je Auftrag eine gestrichelte Verbindung, jede Route eine Farbe mit Pfeilen."""
    xs = [p[0] for p in inst.pts]
    ys = [p[1] for p in inst.pts]
    pad = 0.1 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    for i in range(inst.m):
        a, b = inst.pts[M.pickup(i)], inst.pts[M.delivery(i)]
        fig.add_trace(go.Scatter(x=[a[0], b[0]], y=[a[1], b[1]], mode="lines", line=dict(color="rgba(120,120,120,0.55)", width=1.5, dash="dot"), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.pts[0]] + [inst.pts[s] for s in route] + [inst.pts[0]]
        color = C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", line=dict(color=color, width=3),
                                 marker=dict(symbol="arrow", size=11, angleref="previous", color=color), name=f"Route {r + 1} (Länge {M.route_length(inst, route):.1f})", hoverinfo="skip"))
    for kind, offset, symbol, label in (("Abholen", 1, "triangle-up", "A"), ("Liefern", 2, "triangle-down", "L")):
        idx = [offset + 2 * i for i in range(inst.m)]
        fig.add_trace(go.Scatter(x=[inst.pts[s][0] for s in idx], y=[inst.pts[s][1] for s in idx], mode="markers+text", text=[f"{label}{i + 1}" for i in range(inst.m)], textposition="top center",
                                 marker=dict(symbol=symbol, size=[11 + 3 * q for q in inst.q], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
                                 customdata=[[inst.q[i]] for i in range(inst.m)], hovertemplate=kind + " %{text}: Last %{customdata[0]}<extra></extra>", name=f"{kind} (Größe = Last)"))
    fig.add_trace(go.Scatter(x=[inst.pts[0][0]], y=[inst.pts[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig = _base(fig, 380 if legend else 300)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def build_gap_histogram(costs, opt, bins: int = 20):
    """Verteilung der Splitkosten aller Auftragsfolgen (Lücke zum Optimum in Prozent) als Säulen; die Säule bei 0 sind die optimalen Folgen."""
    gaps = [100.0 * (c / opt - 1.0) for c in costs]
    top = max(gaps)
    width = top / bins if top > 1e-9 else 1.0
    counts = [0] * (bins + 1)
    for g in gaps:
        counts[min(bins, int(g / width + 1e-9))] += 1
    xs = [f"{k * width:.0f}" for k in range(bins + 1)]
    colors = ["#2F6B65"] + ["#9aa5b1"] * bins
    fig = go.Figure(go.Bar(x=xs, y=counts, marker_color=colors, hovertemplate="Lücke ab %{x} %: %{y} Folgen<extra></extra>"))
    fig.update_xaxes(title_text="Lücke des Splits zum Optimum in % (Klassenanfang)")
    fig.update_yaxes(title_text="Zahl der Auftragsfolgen")
    return _base(fig, 320)


def build_positions(options, n_stops: int):
    """Heatmap der Positionspaare (a: Abholen vor Halt a, b: Liefern vor Halt b, b ≥ a): 0 unzulässig, 1 hält die Last, 2 hält Last und Streckengrenze."""
    z = [[None] * (n_stops + 1) for _ in range(n_stops + 1)]
    text = [[""] * (n_stops + 1) for _ in range(n_stops + 1)]
    for a, b, cap, ok, delta in options:
        z[a][b] = 2 if ok else (1 if cap else 0)
        text[a][b] = f"+{delta:.1f}"
    fig = go.Figure(go.Heatmap(z=z, text=text, texttemplate="%{text}", x=list(range(n_stops + 1)), y=list(range(n_stops + 1)), zmin=0, zmax=2, showscale=False, xgap=2, ygap=2,
                               colorscale=[[0.0, "#c9c9c9"], [0.5, "#d8a13a"], [1.0, "#2F6B65"]], hovertemplate="a = %{y}, b = %{x}: %{text}<extra></extra>"))
    fig.update_xaxes(title_text="Liefern an Position b", dtick=1)
    fig.update_yaxes(title_text="Abholen an Position a", dtick=1, autorange="reversed")
    return _base(fig, 360)


def stops_caption(stops) -> str:
    return SP.stops_text(stops)
