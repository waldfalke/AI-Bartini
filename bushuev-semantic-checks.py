"""Arithmetic probes for the reading, not a reproduction of Bushuev's GA.

Run with Python 3. Source locators: bushuev-source-map-20260908.md.
No physics or search-performance claim is established by these assertions.
"""

from fractions import Fraction
from itertools import combinations_with_replacement
from math import hypot


def add(a, b):
    return a[0] + b[0], a[1] + b[1]


def main():
    factors = {"length": (1, 0), "time": (0, 1), "temperature": (5, -4)}
    for a, b in combinations_with_replacement(factors, 2):
        parent = add(factors[a], factors[b])
        assert sum(parent) == 2
        k = 3 - parent[0]
        assert add(parent, (k, -k)) == (3, -1)
        print(f"{a} * {b}: parent={parent}, S=2; V^{k} -> (3,-1)")
    print("All six S=2 coincidences follow from the three input grades S=1.")

    # A missing grade does not specify a unique missing physical quantity.
    missing_candidates = [(0, -1), (-1, 0), (3, -4)]
    assert all(sum(z) == -1 for z in missing_candidates)

    # Formula (6), GA-2011: inherited preference, not measured performance.
    lt_fitness = Fraction(5 + 5 + 1, 3)
    flow_fitness = Fraction(5 + 1 + 1, 3)
    assert lt_fitness > flow_fitness
    assert all(1 <= Fraction(a + b + c, 3) <= 5
               for a in range(1, 6) for b in range(1, 6) for c in range(1, 6))
    print(f"One crossover: L*T fitness={lt_fitness}; volume*frequency={flow_fitness}")

    # Different author metrics can reverse an ordering.
    assert hypot(2, 2) < hypot(3, 0)
    assert 2 + 2 > 3 + 0

    # LT hypothesis: equal geometric-time exposure does not specify a schedule.
    exposure_a = Fraction(20, 1000) * 10
    exposure_b = Fraction(40, 1000) * 5
    assert exposure_a == exposure_b == Fraction(1, 5)
    print(f"20 mm * 10 s = 40 mm * 5 s = {exposure_a} m*s; schedules differ")
    print("PASS: algebra and toy examples only; no GA run or physical experiment.")


if __name__ == "__main__":
    main()
