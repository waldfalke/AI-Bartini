"""Exploratory LT bookkeeping and ideal capillary models; no device validation.

Run: python trial-effects-condensate-check.py
Equations and provenance: trial-effects-condensate-20260908.md.
"""

from math import isclose, sqrt


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def difference(y, x):
    return (y[0] - x[0], y[1] - x[1])


def fold(z, p, q):
    i, a = divmod(z[0], p)
    j, b = divmod(sum(z), q)
    return a, b, i, j


def unfold(state, p, q):
    a, b, i, j = state
    m = a + p * i
    return m, b + q * j - m


def main():
    x, y = (2, -4), (1, 0)
    w = difference(y, x)
    moves = {"L+": (1, 0), "L-": (-1, 0), "T+": (0, 1),
             "T-": (0, -1), "V+": (1, -1), "V-": (-1, 1)}
    for name, shift in moves.items():
        nx, ny = add(x, shift), add(y, shift)
        assert difference(ny, nx) == w == (-1, 4)
        for p, q in ((3, 5), (7, 4)):
            for z in (nx, ny, w):
                assert unfold(fold(z, p, q), p, q) == z
        print(f"{name}: {nx} -> {ny}; w={w}")
    # Coincident screen cells must retain their different winding counts.
    assert fold((0, 0), 3, 5)[:2] == fold((3, -3), 3, 5)[:2]
    assert fold((0, 0), 3, 5) != fold((3, -3), 3, 5)

    laplace_w = difference((2, -4), (3, -4))
    flow_w = difference((3, -1), (2, -4))
    assert add(laplace_w, flow_w) == difference((3, -1), (3, -4)) == (0, 3)
    # Four six-direction moves reach w; no three can reach its T exponent 4.
    assert add(moves["V-"], (0, 3)) == w
    print(f"W bookkeeping: NC_L1={sum(map(abs, w))}; six-move distance=4")

    # Assumed water-like parameters, not measurements of a cold panel.
    rho, gamma, mu, gravity, cos_theta = 1000.0, 0.072, 0.001, 9.81, 0.5
    length = 0.1
    rows = []
    for radius in (100e-6, 50e-6):
        head = 2 * gamma * cos_theta / (rho * gravity * radius)
        fill_time = 2 * mu * length**2 / (gamma * radius * cos_theta)
        rows.append((head, fill_time))
        print(f"r={radius * 1e6:.0f} um: static head={head * 100:.3f} cm; "
              f"horizontal 10 cm Washburn fill={fill_time:.3f} s")
    assert isclose(rows[1][0] / rows[0][0], 2)
    assert isclose(rows[1][1] / rows[0][1], 2)
    print(f"Capillary length={sqrt(gamma / (rho * gravity)) * 1000:.3f} mm")
    print("PASS: coordinates, reversible display, composition, model scaling only.")


if __name__ == "__main__":
    main()
