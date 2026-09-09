"""Synthetic one-axis model only; not a validated physical mount.

Run: python trial-precision-shock-mount-check.py
Conditions and provenance: trial-precision-shock-mount-20260908.md.
"""

from math import isclose, log, sqrt


def clipped(value, limit):
    return max(-limit, min(limit, value))


def potential(x, stiffness, limit):
    edge = limit / stiffness
    if abs(x) <= edge:
        return stiffness * x * x / 2
    return limit * abs(x) - limit * limit / (2 * stiffness)


def response(stiffness, damping, limit, dt, damping_limit=float("inf"), duration=4.0):
    """M=1, x(0)=0, v(0)=0.4; F=clip(k*x,+/-S)+clip(c*v,+/-D).

    This defines an abstract passive force law, not its hardware realization.
    RK4; halve dt to check this smooth/piecewise-smooth trajectory numerically.
    """
    x, v = 0.0, 0.4
    peak_x = peak_a = max_energy_gain = 0.0
    previous_energy = v * v / 2
    for _ in range(round(duration / dt)):
        def rhs(position, velocity):
            force = clipped(stiffness * position, limit) + clipped(damping * velocity, damping_limit)
            return velocity, -force

        a = rhs(x, v)
        b = rhs(x + dt * a[0] / 2, v + dt * a[1] / 2)
        c = rhs(x + dt * b[0] / 2, v + dt * b[1] / 2)
        d = rhs(x + dt * c[0], v + dt * c[1])
        peak_a = max(peak_a, *(abs(stage[1]) for stage in (a, b, c, d)))
        x += dt * (a[0] + 2*b[0] + 2*c[0] + d[0]) / 6
        v += dt * (a[1] + 2*b[1] + 2*c[1] + d[1]) / 6
        peak_x = max(peak_x, abs(x))
        energy = v * v / 2 + potential(x, stiffness, limit)
        max_energy_gain = max(max_energy_gain, energy - previous_energy)
        previous_energy = energy
    # E bounds any later displacement: U(x) <= E for this passive law.
    terminal_bound = sqrt(2 * previous_energy / stiffness)
    assert previous_energy < limit * limit / (2 * stiffness)
    assert max_energy_gain < 1e-9
    return peak_x, peak_a, x, v, terminal_bound


def main():
    # Keep the full SI (kg, m, s) exponents when checking the LT projection.
    for r in range(10):
        si = (2, 2-r, -4+r)  # H/v0**r, with H measured in N**2.
        m, n = 3*si[0] + si[1], -2*si[0] + si[2]
        assert (m, n) == (8-r, -8+r)
        i, a = divmod(m, 6)
        j, b = divmod(m+n, 6)
        assert (a+6*i, b+6*j-(a+6*i)) == (m, n)
        if r == 4:
            assert si == (2, -2, 0) and si != (1, 1, -2)  # Not newtons.
    mass, ordinary_accel, tolerance = 1.0, 0.5, 50e-6
    initial_speed, accel_limit, stroke = 0.4, 20.0, 0.005
    k_min = mass * ordinary_accel / tolerance
    assert isclose(k_min, 10000.0)
    omega = sqrt(k_min / mass)
    assert isclose(initial_speed / omega, 0.004)
    assert isclose(initial_speed * omega, 40.0)
    energy = mass * initial_speed**2 / 2
    minimum_stroke = initial_speed**2 / (2 * accel_limit)
    assert isclose(energy, 0.08) and isclose(minimum_stroke, 0.004)
    # Undamped capped spring: stored energy, not dissipated energy.
    force_limit = mass * accel_limit
    capped_stroke = energy / force_limit + force_limit / (2 * k_min)
    assert isclose(capped_stroke, stroke)
    print(f"k_min={k_min:g} N/m; linear spring: peak a=40 m/s^2, stroke=4 mm")
    print(f"E0={energy:g} J; necessary minimum stroke={minimum_stroke*1000:g} mm")
    print(f"Undamped force-capped spring: turning point={capped_stroke*1000:g} mm; no settling")
    reference = response(k_min, 0.0, 1e6, 5e-5, duration=0.1)
    assert abs(reference[0] - 0.004) < 1e-7
    assert abs(reference[1] - 40.0) < 1e-3
    assert reference[4] > tolerance  # Removing damping must not pass the return bound.
    # Independent closed-form check of the ordinary-engineering candidate.
    k, spring_cap, damping, damper_cap = 12000.0, 2.0, 200.0, 17.0
    edge, critical_speed = spring_cap / k, damper_cap / damping
    v1_squared = initial_speed**2 - 2 * (damper_cap * edge + k * edge**2 / 2)
    assert v1_squared > critical_speed**2
    x2 = edge + (v1_squared - critical_speed**2) / (2 * (spring_cap + damper_cap))
    ordinary_peak = x2 + critical_speed / damping - spring_cap / damping**2 * log(1 + damping * critical_speed / spring_cap)
    assert ordinary_peak < stroke and spring_cap + damper_cap < force_limit
    print(f"Ordinary candidate, exact first turning point: {ordinary_peak*1000:.6f} mm")

    # LT candidate: conservative displacement and acceleration bounds from E<=E0.
    lt_bound = energy / 18.0 + 18.0 / (2 * 20000.0)
    lt_accel_bound = 18.0 + 4.0 * initial_speed
    assert lt_bound < stroke and lt_accel_bound < accel_limit
    print(f"LT candidate, analytic bounds: stroke<={lt_bound*1000:.6f} mm, a<={lt_accel_bound:.6f} m/s^2")
    candidates = [("ordinary", 12000.0, 200.0, 2.0, 17.0),
                  ("LT", 20000.0, 4.0, 18.0, float("inf"))]
    for name, stiffness, damping, cap, damper_cap in candidates:
        coarse = response(stiffness, damping, cap, 1e-4, damper_cap)
        fine = response(stiffness, damping, cap, 5e-5, damper_cap)
        assert abs(coarse[0] - fine[0]) < 1e-7
        assert fine[0] < stroke and fine[1] <= accel_limit
        assert fine[4] < tolerance
        assert mass * ordinary_accel / stiffness <= tolerance
        if name == "ordinary":
            assert abs(fine[0] - ordinary_peak) < 1e-7
        else:
            assert fine[0] <= lt_bound and fine[1] <= lt_accel_bound
        print(f"{name}: peak stroke={fine[0]*1000:.6f} mm, peak a={fine[1]:.6f} m/s^2")
        print(f"at 4 s: x={fine[2]:.3e} m, v={fine[3]:.3e} m/s, future |x| bound={fine[4]:.3e} m")
    print("PASS: algebra, defined force-law response, timestep check; no hardware validation")


if __name__ == "__main__":
    main()
