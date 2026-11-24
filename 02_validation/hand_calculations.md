# Beam Designer validation cases

Downward transverse loads are positive. Calculations below exclude member
self-weight unless noted. Steel cases use W12x26 with E = 29,000,000 psi and
Ix = 204 in⁴.

## 1. Simply supported beam, full-span uniform load

- L = 20 ft, w = 1 kip/ft
- RA = RB = wL/2 = 10 kip
- Vmax = wL/2 = 10 kip
- Mmax = wL²/8 = 50.0 kip-ft at 10 ft
- δmax = 5wL⁴/(384EI) = 0.609 in at 10 ft

## 2. Simply supported beam, centered point load

- L = 20 ft, P = 10 kip at 10 ft
- RA = RB = P/2 = 5 kip
- Vmax = 5 kip
- Mmax = PL/4 = 50.0 kip-ft at 10 ft
- δmax = PL³/(48EI) = 0.4866 in at 10 ft

## 3. Cantilever, tip point load

- L = 20 ft, P = 10 kip at 20 ft
- Fixed reaction = 10 kip
- Vmax = 10 kip
- Mmax = PL = 200 kip-ft at the fixed end
- δmax = PL³/(3EI) = 7.787 in at the free end

## 4. Partial distributed load

- Simply supported L = 20 ft
- w = 1 kip/ft from x = 5 ft to x = 15 ft
- Resultant = 10 kip at x = 10 ft
- RA = RB = 5 kip
- Mmax = 37.5 kip-ft at x = 10 ft

## 5. Representative lumber beam

- Simply supported 2x10 Douglas Fir-Larch No. 2
- Actual dimensions 1.5 in × 9.25 in; E = 1,600,000 psi
- Ix = bd³/12 = 98.93 in⁴
- L = 12 ft; w = 0.1 kip/ft
- RA = RB = 0.6 kip
- Mmax = wL²/8 = 1.8 kip-ft
- δmax = 5wL⁴/(384EI) = 0.1787 in

The corresponding automated cases are retained in `tests/test_analysis.py` and
exercise the calculation layer without creating a Tkinter window.
