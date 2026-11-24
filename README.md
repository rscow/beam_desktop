# Beam Designer

A standard-library Python/Tkinter desktop application for educational beam
analysis.

Run it from the project directory:

```text
python3 main.py
```

Run the headless calculation tests:

```text
python3 -m unittest discover -s tests -v
```

The interface recalculates as inputs change and includes beam, shear, moment,
deflection, and cross-section views. It is an educational tool, not final
structural-design software.

Use **File → Save** to write a versioned `.beam.json` design file and
**File → Open** to restore it. Design files retain the member, support, span,
deflection limit, section-view location, self-weight setting, and all loads.

Use **Export results…** to save every calculated station to a CSV table with
x, shear, moment, and deflection columns. The UTF-8 CSV includes units in its
headers and opens directly in Excel.
