"""Konstanten: Regler-Grenzen, Bänder, Farben, Presets und Annahmentext."""

M_MIN, M_MAX, DEFAULT_M = 2, 7, 4
SEED_MAX, DEFAULT_SEED = 999999, 0
Q_MIN, Q_MAX, DEFAULT_Q = 3, 10, 6            # Kapazität des Fahrzeugs (Last der Aufträge: 1 bis 3)
LIMIT_MIN, LIMIT_MAX, LIMIT_STEP, DEFAULT_LIMIT = 30, 100, 5, 50   # Streckengrenze in Prozent der kürzesten Route über alle Aufträge (Hälfte: mindestens zwei Routen)
LOAD_MAX = 3
FAMILIES = ("Handinstanz (4 Aufträge)", "Zufällig verteilt (0 bis 100)")
HAND_FAMILY, RANDOM_FAMILY = 0, 1
DEFAULT_FAMILY = HAND_FAMILY
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
LEVEL_PP = 0.5                                # „gleichauf“: Unterschied unter einem halben Prozentpunkt
EXACT_LIVE_MAX = 7                            # live exakt bis zu dieser Zahl von Aufträgen (Zustands-DP mit 3^m Zuständen)
ENUM_MAX = 7                                  # alle m! Auftragsfolgen aufzählen bis zu dieser Zahl

# Handinstanz (4 Aufträge, Depot (0, 0), Kapazität 3, Streckengrenze 22): zwei Routen zu je zwei Aufträgen
# Auftrag 1: Abholen (3, 0), Liefern (6, 0), Last 2; Auftrag 2: Abholen (0, 3), Liefern (0, 6), Last 2;
# Auftrag 3: Abholen (-3, 0), Liefern (-6, 0), Last 2; Auftrag 4: Abholen (0, -3), Liefern (0, -6), Last 2
HAND_POINTS = ((0.0, 0.0), (3.0, 0.0), (6.0, 0.0), (0.0, 3.0), (0.0, 6.0), (-3.0, 0.0), (-6.0, 0.0), (0.0, -3.0), (0.0, -6.0))
HAND_LOAD = (2, 2, 2, 2)
HAND_Q = 3
HAND_LIMIT = 22.0

# Bänder
BAND_FILE = "afs_bands.json"
BAND_RANDOM_SEQS = 500                        # zufällige Haltefolgen je Instanz (Zulässigkeit)
BAND_FEAS_SIZES = (2, 3, 4, 5, 6, 8)
BAND_ENUM_SIZES = (4, 5, 6, 7)
BAND_ENUM_INSTANCES = 12
BAND_METHOD_SIZES = (6, 7, 8)
BAND_METHOD_INSTANCES = 20
BAND_POSITION_SIZES = (1, 2, 3, 4, 5)
BAND_POSITION_ROUTES = 150
BAND_DOMINANCE_STOPS_M, BAND_DOMINANCE_STOPS_N = 4, 5
BAND_DOMINANCE_REQ_M, BAND_DOMINANCE_REQ_N = 5, 20
BAND_Q, BAND_LIMIT = 6, 50
KS_INSERT = 10                                # Einfügeläufe für „bestes von k“
KS_ORDERS = 100                               # Auftragsfolgen für „bestes von k“

# Verfahren
METHODS = {
    "opt": "Optimum (exakt)",
    "ins1": "Einfügen, eine Zufallsreihenfolge",
    "ins10": "Einfügen, bestes von 10 Reihenfolgen",
    "nn": "Nächster Nachbar auf Aufträgen + Split",
    "rand1": "Eine zufällige Auftragsfolge + Split",
    "rand100": "Bestes von 100 Auftragsfolgen + Split",
}
LIVE_K_INSERT = (1, 30, 10)                   # (kleinster, größter, Voreinstellung)
LIVE_K_ORDERS = (1, 300, 100)

ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")

# Presets (die Zahlen in den Hilfetexten prüft tests/test_claims.py); das erste ist die Voreinstellung
_R = {"family": 1, "depot": 0, "Q": 6, "limit": 50}
PRESETS = {
    "Das Handbeispiel (4 Aufträge)": {"family": 0, "m": 4, "depot": 0, "Q": 6, "limit": 50, "seed": 0},
    "Haltefolge ohne Zerlegung (6 Aufträge)": {**_R, "m": 6, "seed": 3},
    "Das Optimum ist selten (7 Aufträge)": {**_R, "m": 7, "seed": 6},
    "Einfügen gegen Folge (7 Aufträge)": {**_R, "m": 7, "seed": 11},
}
PRESET_HELP = {
    "Das Handbeispiel (4 Aufträge)": "Vier Aufträge auf den vier Achsen um das Depot (Last je 2, Kapazität 3, Streckengrenze 22): Zwei Aufträge in einer Route passen nur bei benachbarten Achsen. Das Optimum ist 30 + 6√5 = 43,42 mit zwei Routen; "
                                      "16 der 24 Auftragsfolgen liefern es, die übrigen 8 kosten 45,71 (eine Zweierroute und zwei einzelne).",
    "Haltefolge ohne Zerlegung (6 Aufträge)": "Sechs Aufträge, zufällige Karte (Seed 3). Von 1000 zufälligen Haltefolgen dieser Instanz lässt sich keine in zulässige Routen zerlegen; die Auftragsfolge 2 5 1 6 4 3 (Seed 1) zerlegt sich dagegen "
                                              "in 5 Routen mit Länge 596,75, 8,6 % über dem Optimum 549,31.",
    "Das Optimum ist selten (7 Aufträge)": "Sieben Aufträge, zufällige Karte (Seed 6), Optimum 651,81 mit 3 Routen. Von 5040 Auftragsfolgen liefern 144 (2,9 %) das Optimum; eine zufällige Folge liegt im Mittel 24,1 % darüber "
                                           "(Median 26,1 %, schlechteste 47,0 %). Jede dieser Folgen ist zulässig.",
    "Einfügen gegen Folge (7 Aufträge)": "Sieben Aufträge, zufällige Karte (Seed 11), Optimum 532,08. Einfügen in einer Zufallsreihenfolge liegt 20,0 % darüber, nächster Nachbar + Split 51,7 %, eine zufällige Auftragsfolge + Split 38,5 %; "
                                         "das beste von 10 Einfügereihenfolgen und das beste von 100 Auftragsfolgen treffen das Optimum.",
}
ASSUMPTIONS_MARKDOWN = """- **Eigene kleine Instanzen:** zufällige Karten (Koordinaten 0 bis 100, Last 1 bis 3, Kapazität 6, Depot in der Mitte oder in der Ecke), höchstens 7 Aufträge live und 8 in den Bändern; keine Li-Lim-Benchmarks, keine echten Auftragsdaten.
- **Streckengrenze ist Pflicht:** ohne sie wäre eine einzige Route durch alle Aufträge optimal (die Zerlegung entfiele und jede Auftragsfolge wäre optimal). Die Grenze ist die Hälfte der kürzesten Route über alle Aufträge (mindestens die längste Einzelroute); sie ist Teil des Modells, keine Beobachtung.
- **Exaktes Optimum nur klein:** ein DP über 3^m Zustände (Status je Auftrag, letzter Halt) liefert für jede Auftragsmenge die kürzeste Route; der Blockpreis „kürzeste Route der Menge“ ist exakt nur bei kleinen Mengen. Bei großen Instanzen braucht er eine Heuristik, und die Dominanz gilt dann nicht mehr für den Preis.
- **Zufallsverfahren:** „bestes von k Folgen“ ist ein Zufallsverfahren mit festem Seed; eine genetische Suche über Auftragsfolgen ist nicht gemessen.
- **Einfügen ist eine einfache Fassung:** billigste zulässige Stelle für Abholen und Liefern, Aufträge in zufälliger Reihenfolge, sonst neue Route; kein Neuordnen bestehender Routen, keine Nachbarschaften.
- **Keine Fenster, keine Fahrtzeitgrenzen je Auftrag:** nur Kapazität, Streckengrenze und die Reihenfolge Abholen vor Liefern; Wartezeiten und Personenverkehr kommen nicht vor.
- **Ein Lauf je Instanz:** Mediane, Anteile und Zählungen über 20 Instanzen (12 bei der Aufzählung); die Mittelwerte tragen die Streuung der Instanz.
"""
