"""Tkinter user interface for Beam Designer."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .analysis import AnalysisInput, AxialLoad, PointLoad, UniformLoad, analyze
from .catalog import CATALOG, Member
from .persistence import SavedDesign, open_design, save_design
from .report_pdf import create_calculation_sheet
from .results_export import export_results_csv


NAVY = "#17324d"
BLUE = "#2874a6"
RED = "#b42318"
GREEN = "#1f7a4d"
GOLD = "#8a5c00"
PURPLE = "#6a3d9a"
GRID = "#ccd7df"
MUTED = "#657783"
PANEL = "#fbfcfd"


class BeamDesignerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Beam Designer")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.result = None
        self.current_member: Member | None = None
        self.current_inputs: AnalysisInput | None = None
        self.point_rows: list[dict[str, object]] = []
        self.axial_rows: list[dict[str, object]] = []
        self.selected_axial = 0
        self._pending: str | None = None
        self._style()
        self._build_menu()
        self._build()
        self._bind_variables()
        self._populate_members()
        self.section_var.set(10.0)
        self.schedule_calculation()

    def _style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Header.TFrame", background=NAVY)
        style.configure("Header.TLabel", background=NAVY, foreground="white")
        style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("TkDefaultFont", 10))
        style.configure("Section.TLabel", foreground=NAVY, font=("TkDefaultFont", 11, "bold"))
        style.configure("Metric.TLabel", font=("TkDefaultFont", 11, "bold"), foreground=NAVY)
        style.configure("Pass.TLabel", foreground=GREEN, font=("TkDefaultFont", 10, "bold"))
        style.configure("Fail.TLabel", foreground=RED, font=("TkDefaultFont", 10, "bold"))
        style.configure("Status.TLabel", foreground=MUTED)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Save…", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Open…", accelerator="Ctrl+O", command=self.open_file)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.configure(menu=menu)
        self.root.bind_all("<Control-o>", lambda _event: self.open_file())
        self.root.bind_all("<Control-s>", lambda _event: self.save_file())

    def _build(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Beam Designer", style="Header.TLabel", font=("TkDefaultFont", 19, "bold")).pack(anchor="w")
        ttk.Label(header, text="Educational shear, moment, and deflection analysis", style="Header.TLabel").pack(anchor="w")

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        sidebar_host = ttk.Frame(body, width=340)
        output = ttk.Frame(body)
        body.add(sidebar_host, weight=0)
        body.add(output, weight=1)
        self._build_sidebar(sidebar_host)
        self._build_output(output)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Separator(self.root).pack(fill="x")
        ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel", padding=(12, 6)).pack(fill="x")

    def _build_sidebar(self, host: ttk.Frame) -> None:
        canvas = tk.Canvas(host, highlightthickness=0, width=330)
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        panel = ttk.Frame(canvas, padding=(4, 0, 10, 10))
        window_id = canvas.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))

        ttk.Label(panel, text="Beam and loads", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.support_var = tk.StringVar(value="Simply supported")
        self.span_var = tk.StringVar(value="20")
        self.material_var = tk.StringVar(value="Steel W-shapes")
        self.member_var = tk.StringVar()
        self.udl_var = tk.StringVar(value="1")
        self.udl_mode_var = tk.StringVar(value="Full span")
        self.udl_start_var = tk.StringVar(value="5")
        self.udl_end_var = tk.StringVar(value="15")
        self.self_weight_var = tk.BooleanVar(value=True)
        self.deflection_limit_var = tk.StringVar(value="360")

        self._labeled_combo(panel, "Support condition", self.support_var, ("Simply supported", "Cantilever, fixed at left"))
        self._labeled_entry(panel, "Span", self.span_var, "ft")
        self._labeled_combo(panel, "Member table", self.material_var, tuple(CATALOG))
        self.member_combo = self._labeled_combo(panel, "Member", self.member_var, ())
        self._labeled_entry(panel, "Deflection limit", self.deflection_limit_var, "L / ratio")

        ttk.Label(panel, text="Point loads", style="Section.TLabel").pack(anchor="w", pady=(14, 4))
        self.point_container = ttk.Frame(panel)
        self.point_container.pack(fill="x")
        self.point_button = ttk.Button(panel, text="Add point load", command=self.add_point_load)
        self.point_button.pack(fill="x", pady=(4, 0))

        ttk.Label(panel, text="Axial loads", style="Section.TLabel").pack(anchor="w", pady=(14, 4))
        self.axial_container = ttk.Frame(panel)
        self.axial_container.pack(fill="x")
        self.axial_button = ttk.Button(panel, text="Add axial load", command=self.add_axial_load)
        self.axial_button.pack(fill="x", pady=(4, 0))

        ttk.Label(panel, text="Uniform load", style="Section.TLabel").pack(anchor="w", pady=(14, 4))
        self._labeled_entry(panel, "Magnitude", self.udl_var, "kip/ft")
        self._labeled_combo(panel, "Load extent", self.udl_mode_var, ("Full span", "Partial span"))
        self.range_frame = ttk.Frame(panel)
        self.range_frame.pack(fill="x")
        self._labeled_entry(self.range_frame, "Start", self.udl_start_var, "ft")
        self._labeled_entry(self.range_frame, "End", self.udl_end_var, "ft")
        self.range_frame.pack_forget()
        ttk.Checkbutton(panel, text="Include beam self-weight", variable=self.self_weight_var).pack(anchor="w", pady=(8, 0))
        self.source_var = tk.StringVar()
        ttk.Label(panel, textvariable=self.source_var, wraplength=300, foreground=MUTED).pack(anchor="w", pady=(12, 0))

    def _build_output(self, output: ttk.Frame) -> None:
        summary = ttk.Frame(output)
        summary.pack(fill="x", pady=(0, 8))
        self.max_shear_var = tk.StringVar(value="—")
        self.max_moment_var = tk.StringVar(value="—")
        self.max_deflection_var = tk.StringVar(value="—")
        for column, (title, variable) in enumerate((
            ("Maximum shear", self.max_shear_var),
            ("Maximum moment", self.max_moment_var),
            ("Maximum deflection", self.max_deflection_var),
        )):
            card = ttk.LabelFrame(summary, text=title, padding=8)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 4, 0))
            ttk.Label(card, textvariable=variable, style="Metric.TLabel").pack(anchor="w")
            summary.columnconfigure(column, weight=1)

        checks = ttk.Frame(output)
        checks.pack(fill="x", pady=(0, 8))
        self.bending_var = tk.StringVar(value="Bending —")
        self.deflection_var = tk.StringVar(value="Deflection —")
        self.bending_label = ttk.Label(checks, textvariable=self.bending_var, padding=8)
        self.deflection_label = ttk.Label(checks, textvariable=self.deflection_var, padding=8)
        self.bending_label.pack(side="left", fill="x", expand=True)
        self.deflection_label.pack(side="left", fill="x", expand=True)

        section_controls = ttk.Frame(output)
        section_controls.pack(fill="x", pady=(0, 8))
        ttk.Label(section_controls, text="Cross-section location:").pack(side="left")
        self.section_var = tk.DoubleVar(value=10)
        self.section_scale = ttk.Scale(section_controls, from_=0, to=20, variable=self.section_var, command=lambda _value: self.schedule_calculation())
        self.section_scale.pack(side="left", fill="x", expand=True, padx=8)
        self.section_entry_var = tk.StringVar(value="10.0")
        section_entry = ttk.Entry(section_controls, textvariable=self.section_entry_var, width=7)
        section_entry.pack(side="left")
        ttk.Label(section_controls, text="ft").pack(side="left", padx=(3, 0))
        ttk.Button(section_controls, text="Export results…", command=self.export_results).pack(side="left", padx=(12, 0))
        ttk.Button(section_controls, text="Calculation sheet…", command=self.save_calculation_sheet).pack(side="left", padx=(6, 0))
        section_entry.bind("<Return>", self._section_entry_changed)
        section_entry.bind("<FocusOut>", self._section_entry_changed)

        self.notebook = ttk.Notebook(output)
        self.notebook.pack(fill="both", expand=True)
        self.canvases: dict[str, tk.Canvas] = {}
        for key, title in (("beam", "Beam"), ("shear", "Shear"), ("moment", "Moment"), ("deflection", "Deflection"), ("section", "Cross section")):
            frame = ttk.Frame(self.notebook)
            canvas = tk.Canvas(frame, background="white", highlightbackground=GRID, highlightthickness=1)
            canvas.pack(fill="both", expand=True, padx=5, pady=5)
            canvas.bind("<Configure>", lambda _event: self.schedule_calculation())
            self.notebook.add(frame, text=title)
            self.canvases[key] = canvas
        self.canvases["section"].bind("<Button-1>", self._section_clicked)

    def _labeled_entry(self, parent: ttk.Frame, label: str, variable: tk.Variable, unit: str) -> ttk.Entry:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(6, 2))
        row = ttk.Frame(parent)
        row.pack(fill="x")
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Label(row, text=unit, width=7).pack(side="left", padx=(5, 0))
        return entry

    def _labeled_combo(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: tuple[str, ...]) -> ttk.Combobox:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(6, 2))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.pack(fill="x")
        return combo

    def _bind_variables(self) -> None:
        variables = (
            self.support_var, self.span_var, self.member_var, self.udl_var,
            self.udl_start_var, self.udl_end_var, self.self_weight_var, self.deflection_limit_var,
        )
        for variable in variables:
            variable.trace_add("write", lambda *_args: self.schedule_calculation())
        self.material_var.trace_add("write", lambda *_args: self._populate_members())
        self.udl_mode_var.trace_add("write", lambda *_args: self._uniform_mode_changed())
        self.section_var.trace_add("write", lambda *_args: self._section_scale_changed())

    def _populate_members(self) -> None:
        members = CATALOG[self.material_var.get()]
        self.member_combo.configure(values=tuple(member.name for member in members))
        self.member_var.set(members[0].name)

    def _uniform_mode_changed(self) -> None:
        if self.udl_mode_var.get() == "Partial span":
            self.range_frame.pack(fill="x", before=self.range_frame.master.winfo_children()[-2])
        else:
            self.range_frame.pack_forget()
        self.schedule_calculation()

    def add_point_load(self, magnitude: str = "", position: str = "") -> None:
        if len(self.point_rows) >= 5:
            return
        frame = ttk.Frame(self.point_container, padding=(0, 3))
        frame.pack(fill="x")
        magnitude_var = tk.StringVar(value=magnitude)
        position_var = tk.StringVar(value=position)
        ttk.Entry(frame, textvariable=magnitude_var, width=9).pack(side="left", fill="x", expand=True)
        ttk.Label(frame, text="kip @").pack(side="left", padx=3)
        ttk.Entry(frame, textvariable=position_var, width=8).pack(side="left", fill="x", expand=True)
        ttk.Label(frame, text="ft").pack(side="left", padx=(3, 5))
        row: dict[str, object] = {"frame": frame, "magnitude": magnitude_var, "position": position_var}
        ttk.Button(frame, text="×", width=3, command=lambda: self._remove_row(self.point_rows, row)).pack(side="left")
        for variable in (magnitude_var, position_var):
            variable.trace_add("write", lambda *_args: self.schedule_calculation())
        self.point_rows.append(row)
        self.point_button.configure(state="disabled" if len(self.point_rows) >= 5 else "normal")
        self.schedule_calculation()

    def add_axial_load(
        self,
        direction_value: str = "Compression",
        magnitude_value: str = "",
        position_value: str = "",
        offset_x_value: str = "0",
        offset_y_value: str = "0",
    ) -> None:
        if len(self.axial_rows) >= 5:
            return
        outer = ttk.LabelFrame(self.axial_container, text=f"Axial load {len(self.axial_rows) + 1}", padding=5)
        outer.pack(fill="x", pady=3)
        direction = tk.StringVar(value=direction_value)
        magnitude = tk.StringVar(value=magnitude_value)
        position = tk.StringVar(value=position_value)
        offset_x = tk.StringVar(value=offset_x_value)
        offset_y = tk.StringVar(value=offset_y_value)
        top = ttk.Frame(outer)
        top.pack(fill="x")
        ttk.Combobox(top, textvariable=direction, values=("Tension", "Compression"), state="readonly", width=11).pack(side="left")
        ttk.Entry(top, textvariable=magnitude, width=7).pack(side="left", padx=(5, 2))
        ttk.Label(top, text="kip").pack(side="left")
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(4, 0))
        for label, variable in (("x ft", position), ("ex in", offset_x), ("ey in", offset_y)):
            ttk.Label(bottom, text=label).pack(side="left", padx=(4, 2))
            ttk.Entry(bottom, textvariable=variable, width=6).pack(side="left")
        row: dict[str, object] = {
            "frame": outer, "direction": direction, "magnitude": magnitude,
            "position": position, "offset_x": offset_x, "offset_y": offset_y,
        }
        ttk.Button(top, text="×", width=3, command=lambda: self._remove_row(self.axial_rows, row)).pack(side="right")
        outer.bind("<Button-1>", lambda _event, selected=row: self._select_axial(selected))
        for variable in (direction, magnitude, position, offset_x, offset_y):
            variable.trace_add("write", lambda *_args: self.schedule_calculation())
        self.axial_rows.append(row)
        self.selected_axial = len(self.axial_rows) - 1
        self.axial_button.configure(state="disabled" if len(self.axial_rows) >= 5 else "normal")
        self.schedule_calculation()

    def _remove_row(self, rows: list[dict[str, object]], row: dict[str, object]) -> None:
        row["frame"].destroy()  # type: ignore[union-attr]
        rows.remove(row)
        self.selected_axial = min(self.selected_axial, max(0, len(self.axial_rows) - 1))
        self.point_button.configure(state="normal")
        self.axial_button.configure(state="normal")
        self.schedule_calculation()

    def _select_axial(self, row: dict[str, object]) -> None:
        if row in self.axial_rows:
            self.selected_axial = self.axial_rows.index(row)
            self.schedule_calculation()

    def _float(self, variable: tk.Variable, label: str, empty: float = 0.0) -> float:
        text = str(variable.get()).strip()
        if not text:
            return empty
        try:
            return float(text)
        except ValueError as error:
            raise ValueError(f"{label} must be a number.") from error

    def _read_inputs(self) -> AnalysisInput:
        span = self._float(self.span_var, "Span")
        members = CATALOG[self.material_var.get()]
        member = next(member for member in members if member.name == self.member_var.get())
        points = tuple(
            PointLoad(self._float(row["magnitude"], "Point-load magnitude"), self._float(row["position"], "Point-load position"))  # type: ignore[arg-type]
            for row in self.point_rows
            if str(row["magnitude"].get()).strip()  # type: ignore[union-attr]
        )
        end = span if self.udl_mode_var.get() == "Full span" else self._float(self.udl_end_var, "Uniform-load end")
        uniform = UniformLoad(
            self._float(self.udl_var, "Uniform-load magnitude"),
            0 if self.udl_mode_var.get() == "Full span" else self._float(self.udl_start_var, "Uniform-load start"),
            end,
        )
        axials = tuple(
            AxialLoad(
                self._float(row["magnitude"], "Axial-load magnitude"),  # type: ignore[arg-type]
                self._float(row["position"], "Axial-load position"),  # type: ignore[arg-type]
                str(row["direction"].get()) == "Tension",  # type: ignore[union-attr]
                self._float(row["offset_x"], "Horizontal offset"),  # type: ignore[arg-type]
                self._float(row["offset_y"], "Vertical offset"),  # type: ignore[arg-type]
            )
            for row in self.axial_rows
            if str(row["magnitude"].get()).strip()  # type: ignore[union-attr]
        )
        return AnalysisInput(
            support="simple" if self.support_var.get() == "Simply supported" else "cantilever",
            span_ft=span,
            member=member,
            point_loads=points,
            uniform_load=uniform,
            axial_loads=axials,
            include_self_weight=self.self_weight_var.get(),
            deflection_limit_ratio=self._float(self.deflection_limit_var, "Deflection limit ratio"),
        )

    def schedule_calculation(self) -> None:
        if self._pending:
            self.root.after_cancel(self._pending)
        self._pending = self.root.after(90, self.calculate)

    def calculate(self) -> None:
        self._pending = None
        try:
            inputs = self._read_inputs()
            result = analyze(inputs)
        except (ValueError, KeyError, StopIteration) as error:
            self.status_var.set(f"Input error: {error}")
            return
        self.current_inputs = inputs
        self.current_member = inputs.member
        self.result = result
        span = inputs.span_ft
        self.section_scale.configure(to=span)
        section = max(0.0, min(float(self.section_var.get()), span))
        if section != self.section_var.get():
            self.section_var.set(section)
        self.section_entry_var.set(f"{section:.2f}")

        self.max_shear_var.set(f"{result.max_shear_kip:.2f} kip at {result.max_shear_location_ft:.2f} ft")
        self.max_moment_var.set(f"{result.max_moment_kip_ft:.2f} kip-ft at {result.max_moment_location_ft:.2f} ft")
        self.max_deflection_var.set(f"{result.max_deflection_in:.3f} in at {result.max_deflection_location_ft:.2f} ft")
        allow = inputs.member.allowable_bending / 1000
        self.bending_var.set(f"{'PASS' if result.bending_passes else 'FAIL'} — Bending {result.combined_stress_ksi:.2f}/{allow:.2f} ksi ({result.bending_utilization:.0%})")
        self.deflection_var.set(f"{'PASS' if result.deflection_passes else 'FAIL'} — Deflection L/{inputs.deflection_limit_ratio:g}: {result.max_deflection_in:.3f}/{result.deflection_limit_in:.3f} in ({result.deflection_utilization:.0%})")
        self.bending_label.configure(style="Pass.TLabel" if result.bending_passes else "Fail.TLabel")
        self.deflection_label.configure(style="Pass.TLabel" if result.deflection_passes else "Fail.TLabel")
        self.source_var.set(f"{inputs.member.source}\n{inputs.member.assumptions}")
        self.status_var.set("Analysis updated. Downward loads are positive; diagrams use the sign convention shown by their axes.")
        self._draw_all(section)

    def save_file(self) -> None:
        try:
            inputs = self._read_inputs()
            design = SavedDesign.from_analysis(inputs, self.material_var.get(), float(self.section_var.get()))
            design.analysis_input()
        except (ValueError, KeyError, StopIteration) as error:
            messagebox.showerror("Cannot save design", str(error), parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save beam design",
            defaultextension=".beam.json",
            filetypes=(("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            save_design(path, design)
        except OSError as error:
            messagebox.showerror("Cannot save design", str(error), parent=self.root)
            return
        self.status_var.set(f"Saved design to {path}")

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open beam design",
            filetypes=(("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            design = open_design(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot open design", str(error), parent=self.root)
            return
        self._apply_design(design)
        self.status_var.set(f"Opened design from {path}")

    def export_results(self) -> None:
        try:
            result = analyze(self._read_inputs())
        except (ValueError, KeyError, StopIteration) as error:
            messagebox.showerror("Cannot export results", str(error), parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export beam results",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            export_results_csv(path, result)
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot export results", str(error), parent=self.root)
            return
        self.status_var.set(f"Exported {len(result.x_ft)} result rows to {path}")

    def save_calculation_sheet(self) -> None:
        try:
            inputs = self._read_inputs()
            result = analyze(inputs)
            section_location = float(self.section_var.get())
            if not 0 <= section_location <= inputs.span_ft:
                raise ValueError("Cross-section location must be on the beam.")
        except (ValueError, KeyError, StopIteration) as error:
            messagebox.showerror("Cannot create calculation sheet", str(error), parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save calculation sheet",
            defaultextension=".pdf",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            create_calculation_sheet(path, inputs, result, self.material_var.get(), section_location)
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot create calculation sheet", str(error), parent=self.root)
            return
        self.status_var.set(f"Saved calculation sheet to {path}")

    def _apply_design(self, design: SavedDesign) -> None:
        inputs = design.analysis_input()
        for row in self.point_rows + self.axial_rows:
            row["frame"].destroy()  # type: ignore[union-attr]
        self.point_rows.clear()
        self.axial_rows.clear()
        self.point_button.configure(state="normal")
        self.axial_button.configure(state="normal")

        self.support_var.set("Simply supported" if inputs.support == "simple" else "Cantilever, fixed at left")
        self.span_var.set(f"{inputs.span_ft:g}")
        self.material_var.set(design.material_table)
        self.member_var.set(design.member_name)
        self.deflection_limit_var.set(f"{inputs.deflection_limit_ratio:g}")
        self.self_weight_var.set(inputs.include_self_weight)
        uniform = inputs.uniform_load
        uniform_end = inputs.span_ft if uniform.end_ft is None else uniform.end_ft
        full_span = uniform.start_ft == 0 and uniform_end == inputs.span_ft
        self.udl_mode_var.set("Full span" if full_span else "Partial span")
        self.udl_var.set(f"{uniform.magnitude_kip_ft:g}")
        self.udl_start_var.set(f"{uniform.start_ft:g}")
        self.udl_end_var.set(f"{uniform_end:g}")
        for load in inputs.point_loads:
            self.add_point_load(f"{load.magnitude_kip:g}", f"{load.position_ft:g}")
        for load in inputs.axial_loads:
            self.add_axial_load(
                "Tension" if load.tension else "Compression",
                f"{load.magnitude_kip:g}",
                f"{load.position_ft:g}",
                f"{load.horizontal_offset_in:g}",
                f"{load.vertical_offset_in:g}",
            )
        self.section_var.set(design.section_location_ft)
        self.calculate()

    def _section_scale_changed(self) -> None:
        if hasattr(self, "section_entry_var"):
            self.section_entry_var.set(f"{self.section_var.get():.2f}")
        self.schedule_calculation()

    def _section_entry_changed(self, _event: tk.Event) -> None:
        try:
            value = float(self.section_entry_var.get())
            span = float(self.span_var.get())
            self.section_var.set(max(0.0, min(value, span)))
        except ValueError:
            self.status_var.set("Input error: Cross-section location must be a number.")

    def _draw_all(self, section: float) -> None:
        if not self.result or not self.current_inputs:
            return
        self._draw_beam(section)
        self._draw_chart("shear", "Shear (kip)", self.result.shear_kip, BLUE)
        self._draw_chart("moment", "Moment (kip-ft)", self.result.moment_kip_ft, GOLD)
        self._draw_chart("deflection", "Deflection (in)", self.result.deflection_in, PURPLE)
        self._draw_section(section)

    @staticmethod
    def _canvas_size(canvas: tk.Canvas) -> tuple[int, int]:
        return max(canvas.winfo_width(), 500), max(canvas.winfo_height(), 300)

    def _draw_chart(self, key: str, title: str, values: tuple[float, ...], color: str) -> None:
        canvas = self.canvases[key]
        canvas.delete("all")
        width, height = self._canvas_size(canvas)
        left, right, top, bottom = 70, 24, 42, 44
        minimum, maximum = min(min(values), 0), max(max(values), 0)
        if abs(maximum - minimum) < 1e-12:
            minimum, maximum = -1, 1
        plot_width, plot_height = width - left - right, height - top - bottom
        map_x = lambda value: left + value / self.current_inputs.span_ft * plot_width  # type: ignore[union-attr]
        map_y = lambda value: top + (maximum - value) / (maximum - minimum) * plot_height
        zero = map_y(0)
        canvas.create_text(left, 20, text=title, anchor="w", fill=NAVY, font=("TkDefaultFont", 11, "bold"))
        canvas.create_line(left, zero, width - right, zero, fill=MUTED)
        canvas.create_line(left, top, left, height - bottom, fill=GRID)
        points: list[float] = []
        for x, value in zip(self.result.x_ft, values):  # type: ignore[union-attr]
            points.extend((map_x(x), map_y(value)))
        canvas.create_line(*points, fill=color, width=2, smooth=False)
        canvas.create_text(left - 8, map_y(maximum), text=f"{maximum:.2f}", anchor="e", fill=MUTED)
        canvas.create_text(left - 8, map_y(minimum), text=f"{minimum:.2f}", anchor="e", fill=MUTED)
        canvas.create_text(left, height - 18, text="0 ft", anchor="w", fill=MUTED)
        canvas.create_text(width - right, height - 18, text=f"{self.current_inputs.span_ft:.1f} ft", anchor="e", fill=MUTED)  # type: ignore[union-attr]

    def _draw_beam(self, section: float) -> None:
        canvas = self.canvases["beam"]
        canvas.delete("all")
        width, height = self._canvas_size(canvas)
        left, right, beam_y = 70, 35, height * .52
        beam_length = width - left - right
        position_x = lambda ft: left + ft / self.current_inputs.span_ft * beam_length  # type: ignore[union-attr]
        canvas.create_text(left, 22, text="Beam diagram", anchor="w", fill=NAVY, font=("TkDefaultFont", 11, "bold"))
        canvas.create_line(left, beam_y, width - right, beam_y, fill=NAVY, width=8)
        if self.current_inputs.support == "simple":  # type: ignore[union-attr]
            for support_x in (left, width - right):
                canvas.create_polygon(support_x, beam_y + 6, support_x - 13, beam_y + 25, support_x + 13, beam_y + 25, fill=MUTED)
        else:
            canvas.create_rectangle(left - 10, beam_y - 25, left, beam_y + 25, fill=MUTED, outline="")
            for offset in range(-23, 24, 8):
                canvas.create_line(left - 17, beam_y + offset + 7, left - 10, beam_y + offset, fill=MUTED)
        uniform = self.current_inputs.uniform_load  # type: ignore[union-attr]
        uniform_end = self.current_inputs.span_ft if uniform.end_ft is None else uniform.end_ft  # type: ignore[union-attr]
        if self.current_inputs.include_self_weight:  # type: ignore[union-attr]
            canvas.create_line(left, beam_y - 45, width - right, beam_y - 45, fill=MUTED, width=2)
            for arrow_x in range(int(left) + 7, int(width - right), 24):
                canvas.create_line(arrow_x, beam_y - 43, arrow_x, beam_y - 9, fill=MUTED, arrow="last")
            canvas.create_text(width - right, beam_y - 51, text="self-weight", anchor="e", fill=MUTED)
        if uniform.magnitude_kip_ft:
            x1, x2 = position_x(uniform.start_ft), position_x(uniform_end)
            canvas.create_line(x1, beam_y - 69, x2, beam_y - 69, fill=BLUE, width=4)
            for arrow_x in range(int(x1) + 7, int(x2), 18):
                canvas.create_line(arrow_x, beam_y - 67, arrow_x, beam_y - 9, fill=BLUE, arrow="last")
        for load in self.current_inputs.point_loads:  # type: ignore[union-attr]
            x = position_x(load.position_ft)
            canvas.create_line(x, beam_y - 80, x, beam_y - 9, fill=RED, width=2, arrow="last")
            canvas.create_text(x, beam_y - 88, text=f"{load.magnitude_kip:g} kip", fill=RED)
        for load in self.current_inputs.axial_loads:  # type: ignore[union-attr]
            x = position_x(load.position_ft)
            color = GREEN if load.tension else RED
            direction = -1 if load.tension else 1
            canvas.create_line(x - 8, beam_y - 35, x - 30 * direction, beam_y - 35, arrow="last", fill=color, width=2)
            canvas.create_line(x + 8, beam_y - 35, x + 30 * direction, beam_y - 35, arrow="last", fill=color, width=2)
            canvas.create_oval(x - 9, beam_y - 44, x + 9, beam_y - 26, fill=color, outline="white")
            canvas.create_text(x, beam_y - 35, text="T" if load.tension else "C", fill="white", font=("TkDefaultFont", 8, "bold"))
        marker_x = position_x(section)
        canvas.create_line(marker_x, beam_y - 92, marker_x, beam_y + 13, fill=PURPLE, dash=(5, 4), width=2)
        canvas.create_text(marker_x, beam_y - 101, text=f"x = {section:.2f} ft", fill=PURPLE)
        canvas.create_text(left, height - 24, text="0 ft", anchor="w", fill=MUTED)
        canvas.create_text(width - right, height - 24, text=f"{self.current_inputs.span_ft:.1f} ft", anchor="e", fill=MUTED)  # type: ignore[union-attr]

    def _draw_section(self, section: float) -> None:
        canvas = self.canvases["section"]
        canvas.delete("all")
        width, height = self._canvas_size(canvas)
        member = self.current_member
        if not member or not self.result:
            return
        index = self.result.nearest_index(section)
        moment = self.result.moment_kip_ft[index]
        shear = self.result.shear_kip[index]
        bending = moment * 12 / member.sx
        shear_area = member.depth * member.web_thickness if member.material == "steel" and member.web_thickness else member.area
        average_shear = shear / shear_area
        cx, cy, section_height = min(210, width * .28), height * .43, min(220, height * .48)
        scale = section_height / member.depth
        section_width = max(28, member.width * scale)
        self._section_bounds = (cx - section_width / 2, cy - section_height / 2, cx + section_width / 2, cy + section_height / 2)
        canvas.create_text(20, 22, text="Cross-section stresses", anchor="w", fill=NAVY, font=("TkDefaultFont", 11, "bold"))
        if member.material == "steel":
            flange_height = max(5, member.flange_thickness * scale)  # type: ignore[operator]
            web_width = max(6, member.web_thickness * scale)  # type: ignore[operator]
            canvas.create_rectangle(cx - section_width / 2, cy - section_height / 2, cx + section_width / 2, cy - section_height / 2 + flange_height, fill="#dce9f2", outline=NAVY, width=2)
            canvas.create_rectangle(cx - web_width / 2, cy - section_height / 2 + flange_height, cx + web_width / 2, cy + section_height / 2 - flange_height, fill="#a9c8dd", outline=NAVY, width=2)
            canvas.create_rectangle(cx - section_width / 2, cy + section_height / 2 - flange_height, cx + section_width / 2, cy + section_height / 2, fill="#dce9f2", outline=NAVY, width=2)
        else:
            canvas.create_rectangle(*self._section_bounds, fill="#d8c9a6", outline=NAVY, width=2)
        canvas.create_line(cx - section_width / 2 - 15, cy, cx + section_width / 2 + 15, cy, fill=MUTED, dash=(4, 4))
        canvas.create_text(cx + section_width / 2 + 25, cy - section_height / 2, text=f"top {bending:+.2f} ksi", anchor="w", fill=RED)
        canvas.create_text(cx + section_width / 2 + 25, cy + section_height / 2, text=f"bottom {-bending:+.2f} ksi", anchor="w", fill=BLUE)

        for row, load in zip(self.axial_rows, self.current_inputs.axial_loads):  # type: ignore[union-attr]
            marker_x = cx + load.horizontal_offset_in / (member.width / 2) * section_width / 2
            marker_y = cy - load.vertical_offset_in / (member.depth / 2) * section_height / 2
            color = GREEN if load.tension else RED
            radius = 8 if self.axial_rows.index(row) == self.selected_axial else 6
            canvas.create_oval(marker_x - radius, marker_y - radius, marker_x + radius, marker_y + radius, fill=color, outline="black" if radius == 8 else "white", width=2)
            canvas.create_text(marker_x, marker_y, text="T" if load.tension else "C", fill="white", font=("TkDefaultFont", 7, "bold"))

        text_x = max(cx + section_width / 2 + 25, width * .48)
        lines = (
            f"Location x = {section:.2f} ft",
            f"M = {moment:+.3f} kip-ft;  fb = M/Sx = {bending:+.3f} ksi",
            f"V = {shear:+.3f} kip;  average educational shear = {average_shear:+.3f} ksi",
            f"Governing combined stress = {self.result.combined_stress_ksi:.3f} ksi",
            "Positive moment: top compression / bottom tension.",
            "Click inside the section to move the selected axial load eccentricity.",
        )
        for line_number, line in enumerate(lines):
            canvas.create_text(text_x, 70 + line_number * 30, text=line, anchor="w", fill=NAVY if line_number < 4 else MUTED)

    def _section_clicked(self, event: tk.Event) -> None:
        if not self.axial_rows or not self.current_member or not hasattr(self, "_section_bounds"):
            return
        left, top, right, bottom = self._section_bounds
        if not (left <= event.x <= right and top <= event.y <= bottom):
            return
        row = self.axial_rows[self.selected_axial]
        ex = (event.x - (left + right) / 2) / ((right - left) / 2) * self.current_member.width / 2
        ey = ((top + bottom) / 2 - event.y) / ((bottom - top) / 2) * self.current_member.depth / 2
        row["offset_x"].set(f"{ex:.2f}")  # type: ignore[union-attr]
        row["offset_y"].set(f"{ey:.2f}")  # type: ignore[union-attr]


def main() -> None:
    root = tk.Tk()
    BeamDesignerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
