# Prompt Log

- Asked: Create a top-level AGENTS.md containing the two requested workflow instructions, then commit all changes without building anything else.
- Changed: Created AGENTS.md with exactly the requested two lines and added this prompts.md entry. Included all existing project changes in the commit as instructed.
- Worked: Yes. The requested files were created and the changes were committed.

- Asked: Update spec.md to describe a Python desktop app using Tkinter without building anything.
- Changed: Created spec.md from the existing beam-design requirements and added explicit Python/Tkinter platform, window layout, UI behavior, canvas rendering, data-bundling, and testability requirements. No application code was built.
- Worked: Yes. The specification now describes the requested Tkinter desktop application.

- Asked: Read spec.md and build the described Python/Tkinter desktop app, using the HTML prototype as the behavioral reference.
- Changed: Built a standard-library Tkinter Beam Designer with live input validation, dynamic point and axial loads, full/partial distributed loads, self-weight, steel and lumber catalogs, simply supported and cantilever analysis, utilization checks, five resizable canvas views, an interactive cross-section selector, documented source data, hand-validation cases, and headless automated tests.
- Worked: Yes. All 8 calculation tests passed, Python compilation passed, and hidden-window Tkinter startup and interaction smoke tests passed.

- Asked: Run every validation case in spec.md against the app's beam calculations and report expected versus actual values in a table.
- Changed: Executed all five retained steel and lumber cases with self-weight disabled, compared reactions, maximum shear, moment, deflection, and locations against closed-form solutions, and corrected stale cantilever and lumber deflection values plus the missing partial-UDL deflection in the retained hand calculations.
- Worked: Yes. All statics values matched at the reported precision; every deflection result was within 0.0000031 in of its closed-form value, and all automated tests passed.

- Asked: Add File-menu Save and Open commands that persist support type, span, section, deflection limit, and loads, after removing Saving designs from the spec's Out of scope section.
- Changed: Confirmed Saving designs was not present in Out of scope, updated the spec to require local design files, added an editable deflection-limit ratio, implemented validated versioned JSON persistence, added File → Save/Open with keyboard shortcuts and error dialogs, restored all beam and load inputs on open, documented the feature, and added persistence and calculation tests.
- Worked: Yes. All 13 automated tests passed, Python compilation passed, and a hidden-window File-menu save/open round-trip restored the complete design successfully.

- Asked: Add an Export results button that saves x, shear, moment, and deflection along the beam to a CSV file that opens in Excel.
- Changed: Added an Export results button that recalculates current inputs and writes every analysis station to a `.csv` file with x (ft), V (kip), M (kip-ft), and deflection (in) columns; used an Excel-friendly UTF-8 BOM and CRLF rows; updated the spec and README; and added export tests.
- Worked: Yes. All 15 automated tests passed, Python compilation passed, and a hidden-window button smoke test exported and reread all 801 result rows successfully.

- Asked: Add a Calculation sheet button that saves the diagrams and checks as a PDF, with inputs at the top, ready to hand in with a design.
- Changed: Added a Calculation sheet button and dependency-free two-page vector PDF generator containing the complete design inputs, governing values, bending and deflection checks, beam/load graphic, shear, moment and deflection diagrams, cross-section stresses, calculation basis, assumptions, limitations, units, sign conventions, generated timestamp, and page numbering; updated the spec and README; and added PDF content and structural-integrity tests.
- Worked: Yes. All 17 automated tests passed, Python compilation passed, a worst-case report render was visually checked, and a hidden-window button smoke test created a valid two-page PDF.
