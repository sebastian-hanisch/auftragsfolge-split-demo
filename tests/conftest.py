"""Gemeinsame Fixtures: die Handinstanz (vier Aufträge auf den Achsen) und eine kleine Instanz, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from afs_model import Instance, hand_instance  # noqa: E402

S5 = math.sqrt(5)
HAND_OPTIMUM = 30 + 6 * S5            # zwei Routen (A1 L1 A2 L2) und (A3 L3 A4 L4) je 15 + sqrt(45) = 15 + 3 sqrt(5)


@pytest.fixture
def hand():
    """Depot (0,0); Auftrag 1: Abholen (3,0), Liefern (6,0); Auftrag 2: (0,3) nach (0,6); Auftrag 3: (-3,0) nach (-6,0); Auftrag 4: (0,-3) nach (0,-6); Last je 2, Kapazität 3, Streckengrenze 22.

    Von Hand: Route (A1 L1 A2 L2) = 3 + 3 + sqrt(45) + 3 + 6 = 15 + 3 sqrt(5) = 21,708 <= 22; gegenüberliegende Achsen (A1 L1 A3 L3) = 3 + 3 + 9 + 3 + 6 = 24 > 22; Optimum = 2 (15 + 3 sqrt(5)) = 43,4164."""
    return hand_instance()


@pytest.fixture
def two():
    """Zwei Aufträge auf einer Geraden: Depot (0,0); Auftrag 1: (1,0) nach (2,0), Last 1; Auftrag 2: (3,0) nach (4,0), Last 1; Kapazität 1, keine Streckengrenze.
    Von Hand: Route (A1 L1 A2 L2) = 1 + 1 + 1 + 1 + 4 = 8 (Last nie über 1)."""
    return Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (4.0, 0.0)), (1, 1), 1, float("inf"))
