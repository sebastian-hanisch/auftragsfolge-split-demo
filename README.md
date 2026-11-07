# Abholen und Liefern: Riesentour über Aufträge – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-auftragsfolge-split-demo.streamlit.app/)** -->

Zehntes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel; gelbes Stück, das prüft, ob das Rückgrat trägt). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt. Dieses Stück fragt, ob das bei **Abholen und Liefern** noch gilt: Ein Auftrag hat einen Abhol- und einen Lieferpunkt, beide gehören in dieselbe Route, Abholen vor Liefern, dazu Kapazität und eine Streckengrenze je Route.

## Kernfrage

Trägt das Rückgrat Riesentour + Split bei Paaren? Die Demo stellt zwei Arten von Riesentouren gegenüber: die Folge aller **Halte** und die Folge der **Aufträge** (Blockpreis = kürzeste Route der Auftragsmenge, wie die Rundreise je Cluster in Stück 6). Sie zeigt eine zufällige Folge auf beiden Ebenen, zählt alle Auftragsfolgen einer Instanz auf, vergleicht Einfügen, nächsten Nachbarn und Folgen mit Split mit dem exakten Optimum und zeigt die Einfügepositionen eines Auftrags. Live bis 7 Aufträge, in den Bändern bis 8.

## Modell

Ein Depot, m Aufträge; Auftrag i hat einen Abholpunkt, einen Lieferpunkt und die Last 1 bis 3, ein Fahrzeug der Kapazität Q (6), euklidische Entfernungen, Koordinaten ganzzahlig 0 bis 100. Eine Route beginnt und endet im Depot, jeder Auftrag liegt ganz in einer Route (Abholen vor Liefern), die Last im Fahrzeug überschreitet nie Q, die Länge nie die **Streckengrenze** (die Hälfte der kürzesten Route über alle Aufträge, mindestens die längste Einzelroute). Ziel: kürzeste Gesamtlänge. **Ohne die Streckengrenze wäre eine einzige Route durch alle Aufträge optimal**: die Zerlegung entfiele, und jede Auftragsfolge wäre optimal (Befund 6).

## Methodik

- **Exaktes Optimum:** ein DP über den Zustand (Status je Auftrag: offen, abgeholt, geliefert; letzter Halt) liefert für jede Auftragsmenge die kürzeste Route (3^m · (2m + 1) Zustände), eine Partitions-DP darüber das Optimum. Bis 8 Aufträge in Sekunden.
- **Haltefolge:** eine Permutation aller 2m Halte; der Split zerlegt sie in zusammenhängende Blöcke, jeder Block muss selbst eine zulässige Route sein.
- **Auftragsfolge:** eine Permutation der m Aufträge; der Split zerlegt sie in Blöcke von Aufträgen, ein Block kostet die kürzeste Route seiner Auftragsmenge. Jeder Auftrag allein ist eine Route: jede Folge ist zerlegbar.
- **Einfügen:** Aufträge nacheinander an der billigsten zulässigen Stelle (Abholen an Position a, Liefern an Position b ≥ a in einer bestehenden Route, Last und Streckengrenze eingehalten), sonst neue Route. **Nächster Nachbar:** Auftragsfolge nach dem nächsten Abholpunkt, dann Split. **Bestes von k Folgen:** k zufällige Auftragsfolgen mit Split (Zufall mit festem Seed).
- **Bänder:** vorberechnet (`generate_precomputed.py`), alle Instanzen deterministisch aus festen Seeds (Kapazität 6, Streckengrenze 50 %), keine Zeiten.

## Befunde (gemessen, keine Behauptungen)

**1. Die Dominanz gilt auf beiden Ebenen.** Das Minimum des Splits über alle Folgen ist das exakte Optimum: für alle 40320 Haltefolgen von 4 Aufträgen in 5 von 5 Instanzen, für alle Auftragsfolgen von 5 Aufträgen in 20 von 20 Instanzen. Aus jeder zulässigen Lösung entsteht durch Aneinanderhängen der Routen eine Folge, deren Split sie wiederfindet.

**2. Auf der Halteebene ist fast jede Folge unzulässig.** Anteil der zufälligen Haltefolgen (je Größe 20 Instanzen mit je 500 Folgen), die sich in zulässige Routen zerlegen lassen:

| Aufträge m | zerlegbare Haltefolgen (mit Streckengrenze) | ohne Streckengrenze (nur Kapazität und Abholen vor Liefern) |
|---|---|---|
| 2 | 8,21 % (821 von 10000) | 25,06 % (2506 von 10000) |
| 3 | 1,06 % (106 von 10000) | 10,69 % (1069 von 10000) |
| 4 | 0,12 % (12 von 10000) | 4,02 % (402 von 10000) |
| 5 | 0,02 % (2 von 10000) | 1,25 % (125 von 10000) |
| 6 | 0,01 % (1 von 10000) | 0,41 % (41 von 10000) |
| 8 | 0,00 % (0 von 10000) | 0,01 % (1 von 10000) |

Ein Chromosom aus Halten braucht Reparatur; der Split allein findet kaum einen Weg. Von den 40320 Haltefolgen von 4 Aufträgen waren in den 5 Instanzen zusammen nur 298 zerlegbar.

**3. Auf der Auftragsebene ist jede Folge zulässig, und das Optimum ist selten wie in Stück 1.** Alle Auftragsfolgen je Instanz (12 Instanzen je Größe):

| Aufträge m | Folgen | optimale Folgen: Median | kleinster / größter Anteil | Lücke einer zufälligen Folge: Mittel | Median |
|---|---|---|---|---|---|
| 4 | 24 | 50,0 % | 50,0 % / 100,0 % | 4,5 % | 3,0 % |
| 5 | 120 | 40,0 % | 20,0 % / 100,0 % | 8,3 % | 8,2 % |
| 6 | 720 | 11,7 % | 6,7 % / 33,3 % | 15,1 % | 15,5 % |
| 7 | 5040 | 3,8 % | 2,9 % / 14,3 % | 17,8 % | 17,0 % |

**4. Verfahren.** Lücke zum exakten Optimum (Prozent des Optimums):

**6 Aufträge, 20 Instanzen:**


| Verfahren | Lücke: Mittel | Median | Maximum | Optimum in |
|---|---|---|---|---|
| Einfügen, eine Reihenfolge | 4,4 % | 0,4 % | 31,2 % | 8 von 20 |
| Einfügen, Mittel von 10 Reihenfolgen | 6,3 % | 5,2 % | 18,8 % | 1 von 20 |
| Einfügen, bestes von 10 | 0,2 % | 0,0 % | 4,2 % | 19 von 20 |
| Nächster Nachbar + Split | 10,3 % | 3,4 % | 66,2 % | 5 von 20 |
| Eine Auftragsfolge + Split | 19,8 % | 18,4 % | 47,3 % | 1 von 20 |
| Bestes von 100 Auftragsfolgen + Split | 0,0 % | 0,0 % | 0,0 % | 20 von 20 |

**7 Aufträge, 20 Instanzen:**


| Verfahren | Lücke: Mittel | Median | Maximum | Optimum in |
|---|---|---|---|---|
| Einfügen, eine Reihenfolge | 7,2 % | 3,0 % | 25,7 % | 6 von 20 |
| Einfügen, Mittel von 10 Reihenfolgen | 7,3 % | 6,1 % | 18,7 % | 0 von 20 |
| Einfügen, bestes von 10 | 0,7 % | 0,0 % | 10,5 % | 16 von 20 |
| Nächster Nachbar + Split | 9,7 % | 9,0 % | 44,7 % | 4 von 20 |
| Eine Auftragsfolge + Split | 20,4 % | 19,1 % | 46,3 % | 0 von 20 |
| Bestes von 100 Auftragsfolgen + Split | 0,0 % | 0,0 % | 0,0 % | 20 von 20 |

**8 Aufträge, 20 Instanzen:**


| Verfahren | Lücke: Mittel | Median | Maximum | Optimum in |
|---|---|---|---|---|
| Einfügen, eine Reihenfolge | 11,1 % | 6,1 % | 35,5 % | 2 von 20 |
| Einfügen, Mittel von 10 Reihenfolgen | 10,6 % | 11,1 % | 19,8 % | 0 von 20 |
| Einfügen, bestes von 10 | 0,6 % | 0,0 % | 6,1 % | 14 von 20 |
| Nächster Nachbar + Split | 15,1 % | 13,6 % | 51,9 % | 0 von 20 |
| Eine Auftragsfolge + Split | 25,0 % | 21,8 % | 62,7 % | 1 von 20 |
| Bestes von 100 Auftragsfolgen + Split | 0,1 % | 0,0 % | 1,2 % | 16 von 20 |

Einfügen in einer Reihenfolge liegt bei 8 Aufträgen 11,1 % über dem Optimum, das beste von 10 Reihenfolgen 0,6 %; der nächste Nachbar + Split 15,1 %; **das beste von 100 zufälligen Auftragsfolgen + Split liegt 0,1 % über dem Optimum und trifft es in 16 von 20 Instanzen**. Die Folge mit Split schlägt das einmalige Einfügen deutlich und ist mit zehn Einfügeläufen gleichauf.

**5. Die Paarbedingung verkleinert die Einfügepositionen mäßig.** Einfügen eines Auftrags in eine zufällige zulässige Route mit k Aufträgen (150 Routen je k):

| Aufträge in der Route k | Halte | Positionspaare (a ≤ b) | davon kapazitätszulässig | Anteil |
|---|---|---|---|---|
| 1 | 2 | 6,0 | 6,0 | 100 % |
| 2 | 4 | 15,0 | 13,2 | 88 % |
| 3 | 6 | 28,0 | 20,1 | 72 % |
| 4 | 8 | 45,0 | 28,2 | 63 % |
| 5 | 10 | 66,0 | 33,6 | 51 % |

Die Zahl der Positionspaare wächst quadratisch mit der Zahl der Halte; kapazitätszulässig bleibt bei 5 Aufträgen noch die Hälfte.

**6. Ohne bindende Streckengrenze ist die Frage leer.** Bei einer Streckengrenze von 100 % der kürzesten Gesamtroute ist eine Route durch alle Aufträge optimal, und 5040 von 5040 Auftragsfolgen (12 Instanzen mit 5 und 6 Aufträgen) liefern das Optimum. Die erste Fassung der Messung ohne Streckengrenze lag genau hier: jede Folge optimal, das Einfügen dagegen nicht.

**Handinstanz** (vier Aufträge auf den vier Achsen um das Depot, Last je 2, Kapazität 3, Streckengrenze 22): zwei Aufträge in einer Route passen nur bei benachbarten Achsen; Optimum 30 + 6√5 = 43,42 mit zwei Routen; 16 der 24 Auftragsfolgen liefern es, die übrigen 8 kosten 45,71.

## Ehrliche Grenzen

- **Eigene kleine Instanzen:** zufällige Karten (Koordinaten 0 bis 100, Last 1 bis 3, Kapazität 6, Depot in der Mitte oder in der Ecke), höchstens 7 Aufträge live und 8 in den Bändern; keine Li-Lim-Benchmarks, keine echten Auftragsdaten.
- **Streckengrenze ist Pflicht:** ohne sie wäre eine einzige Route durch alle Aufträge optimal (die Zerlegung entfiele und jede Auftragsfolge wäre optimal). Die Grenze ist die Hälfte der kürzesten Route über alle Aufträge (mindestens die längste Einzelroute); sie ist Teil des Modells, keine Beobachtung.
- **Exaktes Optimum nur klein:** ein DP über 3^m Zustände (Status je Auftrag, letzter Halt) liefert für jede Auftragsmenge die kürzeste Route; der Blockpreis „kürzeste Route der Menge“ ist exakt nur bei kleinen Mengen. Bei großen Instanzen braucht er eine Heuristik, und die Dominanz gilt dann nicht mehr für den Preis.
- **Zufallsverfahren:** „bestes von k Folgen“ ist ein Zufallsverfahren mit festem Seed; eine genetische Suche über Auftragsfolgen ist nicht gemessen.
- **Einfügen ist eine einfache Fassung:** billigste zulässige Stelle für Abholen und Liefern, Aufträge in zufälliger Reihenfolge, sonst neue Route; kein Neuordnen bestehender Routen, keine Nachbarschaften.
- **Keine Fenster, keine Fahrtzeitgrenzen je Auftrag:** nur Kapazität, Streckengrenze und die Reihenfolge Abholen vor Liefern; Wartezeiten und Personenverkehr kommen nicht vor.
- **Ein Lauf je Instanz:** Mediane, Anteile und Zählungen über 20 Instanzen (12 bei der Aufzählung); die Mittelwerte tragen die Streuung der Instanz.

## Befunde und Korrekturen gegenüber dem Plan

- **Streckengrenze in der Zulässigkeitsmessung:** Die Phase 0 zählte die zulässigen Haltefolgen ohne Streckengrenze auf einer Instanz (25,3 / 12,8 / 6,2 / 2,6 / 1,1 / 0,07 % bei 2, 3, 4, 5, 6, 8 Aufträgen). Die Bänder zählen über 20 Instanzen je Größe mit und ohne Streckengrenze: ohne 25,1 % / 10,7 % / 4,0 % / 1,2 % / 0,41 % / 0,01 %, mit 8,2 % / 1,1 % / 0,12 % / 0,02 % / 0,01 % / 0,00 %. Die Aussage bleibt, nur ist sie mit der Streckengrenze (dem Modell dieser Demo) noch schärfer.
- **Verfahren bei 8 Aufträgen:** Phase 0 hatte 1,1 % (15 von 20) für das beste von 100 Auftragsfolgen und 1,4 % für das beste von 10 Einfügereihenfolgen; die Bänder mit neuen Seeds und eigener Seed-Vergabe geben 0,1 % (16 von 20) und 0,6 %. Die Rangfolge (Folge mit Split ≥ Einfügen ≥ nächster Nachbar) ist dieselbe.
- **Einfügepositionen:** Phase 0 nannte 100 / 89 / 74 / 64 / 50 % kapazitätszulässig (300 Routen), die Bänder mit 150 Routen geben 100 % / 88 % / 72 % / 63 % / 51 %; die Positionspaare (6 / 15 / 28 / 45 / 66) sind unverändert.
- **Live bis 7 statt 8 Aufträge:** der exakte DP rechnet auch 8 Aufträge in unter einer Sekunde, die Aufzählung aller Folgen (8! = 40 320 Splits) und die Verfahren-Tabelle sind aber bis 7 live; die Bänder gehen bis 8.
- **Lehren:** (1) Das Modell muss die Zerlegung erzwingen: ohne Streckengrenze ist jede Folge optimal. (2) Auf Auftragsebene braucht die Folge den Blockpreis (beste Route der Menge), nicht feste Halte. (3) Die Handinstanz mit vier Achsen macht die Zerlegung an der Streckengrenze von Hand nachrechenbar.

## Verifikation

- **Handwerte:** die Handinstanz (Optimum 30 + 6√5 aus Wurzeln, Route 15 + 3√5, die verbotene Gegenüber-Paarung mit Länge 24 > 22), Zulässigkeit von Routen, der Split jeder der 24 Auftragsfolgen (16 optimal, 8 mit 45,71), die Einfügepositionen von Hand (6 Paare, 2 zulässig), zwei Aufträge auf einer Geraden (`tests/test_hand.py`).
- **Orakel:** die exakte Lösung gegen die Aufzählung aller Zerlegungen und aller Halte-Reihenfolgen (bis 3 Aufträge und die Handinstanz mit 4), die Tabelle der kürzesten Routen gegen die Aufzählung, die Dominanz auf beiden Ebenen (alle Folgen), jedes Verfahren liefert gültige Pläne (eigener Prüfer) und nie weniger als das Optimum (`tests/test_oracle.py`).
- **Eigenschaften:** jede Auftragsfolge ist zerlegbar und nie besser als das Optimum; Herausnehmen eines Auftrags verlängert die kürzeste Route nie; mehr Kapazität und eine lockerere Streckengrenze sind nie schlechter; Umnummerieren ändert das Optimum nicht, Skalieren skaliert es; ohne bindende Streckengrenze ist jede Folge optimal; die aneinandergehängten optimalen Routen zerlegen sich zum Optimum (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Aufträge, Kapazität gleich größter Last, kleinste Streckengrenze, Einzelrouten, Einfügen in einen leeren Plan, ein Optimum aus einer Route (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau und gegen eine frische Rechnung von Stichproben (`tests/test_bands.py`). Es werden nie Zeiten gespeichert oder gemessen.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Experimente, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

139 Tests. Laufzeit lokal etwa anderthalb Minuten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Zwischenstände der Rechnung |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `afs_bands.json` | vorberechnete Bänder (Zulässigkeit, Aufzählungen, Verfahren, Dominanz, Einfügepositionen) |
| `afs_constants.py` | Regler-Grenzen, Bänder, Presets, Annahmentext |
| `afs_evaluation.py` | Formate, Bänder, Live-Rechnungen, Verdikt-Logik |
| `afs_heuristics.py` | Einfügen, nächster Nachbar, bestes von k Folgen, Einfügepositionen |
| `afs_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `afs_model.py` | Instanz, exakter DP (kürzeste Route je Auftragsmenge, Optimum), Prüfer |
| `afs_pdf_export.py` | PDF-Export des Ergebnisses |
| `afs_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `afs_split.py` | Split auf Haltefolgen und auf Auftragsfolgen |
| `afs_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `afs_bands.json` (parallel, höchstens 12 Prozesse) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Fahrtzeitgrenzen je Auftrag, Zeitfenster, Wartezeiten:** nur Kapazität, Streckengrenze und die Reihenfolge Abholen vor Liefern.
- **Li-Lim-Benchmarks und echte Auftragsdaten:** nicht geladen; nur kleine Zufallsinstanzen.
- **Mehr als 8 Aufträge:** der Blockpreis „kürzeste Route der Menge“ bräuchte eine Heuristik, die Dominanz gälte dann nicht mehr für den Preis.
- **Genetische Suche, ALNS oder Nachbarschaften über Auftragsfolgen:** nicht gemessen; „bestes von k Folgen“ ist ein Zufallsverfahren.
- **Zeitmessung:** keine Zeiten in den Bändern, keine Zeitaussagen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
