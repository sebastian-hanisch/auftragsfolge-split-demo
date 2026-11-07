"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

import math

from fpdf import FPDF

import afs_constants as C
import afs_model as M
import afs_split as SP
from afs_evaluation import Settings, de, feas_stats, method_gaps, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "‖": "|", "√": "sqrt"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, inst: M.Instance, sol: M.Solution) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Abholen und Liefern: Riesentour über Aufträge"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    where = "Handinstanz (4 Aufträge)" if s.family == C.HAND_FAMILY else f"{s.m} Aufträge, Depot: {C.DEPOTS[s.depot].lower()}, Seed {s.seed}"
    limit = de(inst.Lmax, 1) if math.isfinite(inst.Lmax) else "keine"
    pdf.multi_cell(0, 5, _s(f"{where}. Kapazität {inst.Q}, Last {', '.join(str(x) for x in inst.q)}, Streckengrenze je Route {limit}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _s(f"Optimum: {de(sol.cost)} mit {len(sol.routes)} Routen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    widths = (16, 128, 30)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Route", "Halte", "Länge")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i, r in enumerate(sol.routes, start=1):
        for w, v in zip(widths, (str(i), SP.stops_text(r), de(M.route_length(inst, r)))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _s("Aus den Bändern"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    f4, f6 = feas_stats(4), feas_stats(6)
    g8 = method_gaps(8)
    pdf.multi_cell(0, 5, _s(f"Zerlegbare zufällige Haltefolgen: {pct(f4['p_limit'], 2)} bei 4, {pct(f6['p_limit'], 2)} bei 6 Aufträgen; jede Auftragsfolge ist zerlegbar. Bei 8 Aufträgen: Einfügen einmal {pct(g8['ins1']['mean'])} über dem Optimum, "
                            f"bestes von 100 Auftragsfolgen + Split {pct(g8['rand100']['mean'])}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Streckengrenze ist Teil des Modells (ohne sie wäre eine Route optimal). Kleine Zufallsinstanzen, exakt. Quelle: auftragsfolge-split-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
