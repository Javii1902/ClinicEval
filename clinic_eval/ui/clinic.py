import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from ..db import (
    get_clinic_names,
    rename_clinic,
    get_latest_assessment_for_clinic,
    get_assessments_for_clinic,
    update_assessment_date,
    update_assessment_region,
    update_assessment_specialty,
    get_assessment_detail,
    update_assessment_content,
    get_all_question_comment_templates,
    delete_assessment,
)
from ..validators import is_valid_date, normalize_choice
from .assessment_config import (
    ASSESSMENT_ITEMS,
    TESTS_PERFORMED,
    ANSWER_OPTIONS,
    SPECIALTY_OPTIONS,
    REGION_OPTIONS,
)
from .excel_exports import export_clinic_workbook
from .scroll_utils import bind_mousewheel_scrolling
from .widgets import SearchableCombobox, SelectionEditPopup, QuestionTemplatePopup


class Clinic(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.selected_clinic_var = tk.StringVar()
        self.current_name_var = tk.StringVar(value="—")
        self.current_region_var = tk.StringVar(value="—")
        self.current_specialty_var = tk.StringVar(value="—")
        self.current_date_var = tk.StringVar(value="—")
        self.selected_assessment_var = tk.StringVar()

        self.clinic_combobox = None
        self.assessment_combobox = None
        self.assessment_map = {}
        self.current_assessment_id = None

        self.tests_vars = {}
        self.answer_vars = []
        self.template_preview_widgets = []
        self.manual_comment_widgets = []
        self.question_selected_templates = [[] for _ in range(len(ASSESSMENT_ITEMS))]
        self.question_template_options = []
        self.notes_text = None

        self.canvas = None
        self.scrollbar = None
        self.scrollable_frame = None
        self.canvas_window = None

        self.build_ui()
        self.load_clinic_names()

    def build_ui(self):
        outer_container = ttk.Frame(self)
        outer_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(outer_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(outer_container, orient="vertical", command=self.on_canvas_scroll)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        bind_mousewheel_scrolling(self.canvas)
        # The clinic combobox's dropdown floats in its own Toplevel, so it
        # needs to be repositioned (or hidden once scrolled out of view)
        # whenever this canvas scrolls - on top of the shared scroll
        # handler's own binding.
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(sequence, lambda e: self.reposition_all_dropdowns(), add="+")

        container = ttk.Frame(self.scrollable_frame, padding=12)
        container.pack(fill="both", expand=True)

        header_frame = ttk.Frame(container)
        header_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(header_frame, text="Clinic Management", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(header_frame, text="Refresh", command=self.refresh_data).pack(side="right")

        select_frame = ttk.LabelFrame(container, text="Select Clinic", padding=12)
        select_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(select_frame, text="Clinic:").grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")
        # Same searchable-dropdown widget as the New Assessment tab's clinic
        # field: typing filters a real dropdown list of matches instead of
        # just narrowing a plain combobox's hidden values. Selecting a
        # clinic still only happens via an explicit pick (click, or
        # Down+Enter) - typing alone does not load anything.
        self.clinic_combobox = SearchableCombobox(
            select_frame,
            textvariable=self.selected_clinic_var,
            values=[],
            width=50,
            on_select=self.on_clinic_selected,
            scroll_canvas=self.canvas,
        )
        self.clinic_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        select_frame.columnconfigure(1, weight=1)

        details_frame = ttk.LabelFrame(container, text="Clinic Details", padding=12)
        details_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(details_frame, text="Current Clinic Name:").grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        ttk.Label(details_frame, textvariable=self.current_name_var).grid(row=0, column=1, padx=5, pady=6, sticky="w")
        ttk.Button(details_frame, text="Edit Clinic Name", command=self.edit_clinic_name).grid(row=0, column=2, padx=(12, 0), pady=6, sticky="w")

        ttk.Label(details_frame, text="Region:").grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        ttk.Label(details_frame, textvariable=self.current_region_var).grid(row=1, column=1, padx=5, pady=6, sticky="w")
        ttk.Button(details_frame, text="Edit Region", command=self.edit_region).grid(row=1, column=2, padx=(12, 0), pady=6, sticky="w")

        ttk.Label(details_frame, text="Specialty:").grid(row=2, column=0, padx=(0, 8), pady=6, sticky="w")
        ttk.Label(details_frame, textvariable=self.current_specialty_var).grid(row=2, column=1, padx=5, pady=6, sticky="w")
        ttk.Button(details_frame, text="Edit Specialty", command=self.edit_specialty).grid(row=2, column=2, padx=(12, 0), pady=6, sticky="w")

        ttk.Label(details_frame, text="Assessment Record:").grid(row=3, column=0, padx=(0, 8), pady=6, sticky="w")
        self.assessment_combobox = ttk.Combobox(details_frame, textvariable=self.selected_assessment_var, state="readonly", width=50)
        self.assessment_combobox.grid(row=3, column=1, padx=5, pady=6, sticky="ew")
        self.assessment_combobox.bind("<Button-1>", self.open_combobox_dropdown)
        self.assessment_combobox.bind("<<ComboboxSelected>>", lambda e: self.on_assessment_selected())

        assessment_button_frame = ttk.Frame(details_frame)
        assessment_button_frame.grid(row=3, column=2, padx=(12, 0), pady=6, sticky="w")
        ttk.Button(assessment_button_frame, text="Edit Assessment Date", command=self.edit_assessment_date).pack(side="left")
        ttk.Button(assessment_button_frame, text="Delete Assessment", command=self.delete_selected_assessment).pack(side="left", padx=(8, 0))

        ttk.Label(details_frame, text="Selected Date:").grid(row=4, column=0, padx=(0, 8), pady=6, sticky="w")
        ttk.Label(details_frame, textvariable=self.current_date_var).grid(row=4, column=1, padx=5, pady=6, sticky="w")
        details_frame.columnconfigure(1, weight=1)

        tests_frame = ttk.LabelFrame(container, text="Tests Performed", padding=12)
        tests_frame.pack(fill="x", pady=(0, 10))

        cols = 3
        for i, test_name in enumerate(TESTS_PERFORMED):
            var = tk.BooleanVar(value=False)
            self.tests_vars[test_name] = var
            row = i // cols
            col = i % cols
            ttk.Checkbutton(tests_frame, text=test_name, variable=var).grid(row=row, column=col, padx=5, pady=2, sticky="w")

        for col in range(cols):
            tests_frame.columnconfigure(col, weight=1)

        question_frame = ttk.LabelFrame(container, text="Assessment Detail", padding=12)
        question_frame.pack(fill="both", expand=True, pady=(0, 10))

        content_frame = ttk.Frame(question_frame)
        content_frame.pack(fill="both", expand=True)

        header_labels = ["Item", "Category", "Description", "Answer", "Template Comments", "Manual Comments"]
        for index, label in enumerate(header_labels):
            ttk.Label(content_frame, text=label, font=("Segoe UI", 10, "bold")).grid(row=0, column=index, padx=5, pady=(0, 8), sticky="w")

        content_frame.columnconfigure(0, weight=0, minsize=45)
        content_frame.columnconfigure(1, weight=1, minsize=160)
        content_frame.columnconfigure(2, weight=3, minsize=320)
        content_frame.columnconfigure(3, weight=0, minsize=110)
        content_frame.columnconfigure(4, weight=3, minsize=320)
        content_frame.columnconfigure(5, weight=3, minsize=320)

        self.answer_vars = []
        self.template_preview_widgets = []
        self.manual_comment_widgets = []

        db_templates_by_question = get_all_question_comment_templates()

        for row_index, item in enumerate(ASSESSMENT_ITEMS, start=1):
            ttk.Label(content_frame, text=str(item["number"])).grid(row=row_index, column=0, padx=5, pady=4, sticky="nw")
            ttk.Label(content_frame, text=item["category"], wraplength=160, justify="left").grid(row=row_index, column=1, padx=5, pady=4, sticky="nw")
            ttk.Label(content_frame, text=item["text"], wraplength=350, justify="left").grid(row=row_index, column=2, padx=5, pady=4, sticky="nw")

            answer_var = tk.StringVar(value="")
            self.answer_vars.append(answer_var)
            answer_combo = ttk.Combobox(content_frame, textvariable=answer_var, state="readonly", values=ANSWER_OPTIONS, width=10)
            answer_combo.grid(row=row_index, column=3, padx=5, pady=4, sticky="nw")
            answer_combo.bind("<Button-1>", self.open_combobox_dropdown)

            template_frame = ttk.Frame(content_frame)
            template_frame.grid(row=row_index, column=4, padx=5, pady=4, sticky="nsew")
            ttk.Button(template_frame, text="Edit Templates", command=lambda idx=row_index - 1: self.open_question_template_popup(idx)).pack(fill="x", anchor="w", pady=(0, 4))

            preview_text = tk.Text(template_frame, height=4, width=42, wrap="word")
            preview_text.pack(fill="both", expand=True)
            preview_text.configure(state="disabled")
            self.template_preview_widgets.append(preview_text)

            manual_text = tk.Text(content_frame, height=5, width=42, wrap="word")
            manual_text.grid(row=row_index, column=5, padx=5, pady=4, sticky="nsew")
            self.manual_comment_widgets.append(manual_text)

            default_templates = item.get("templates", []) or []
            saved_templates = db_templates_by_question.get(item["number"], [])
            all_templates = list(dict.fromkeys(default_templates + saved_templates))
            self.question_template_options.append(all_templates)

        notes_frame = ttk.LabelFrame(container, text="Overall Notes", padding=12)
        notes_frame.pack(fill="x", pady=(0, 10))
        self.notes_text = tk.Text(notes_frame, height=8, wrap="word")
        self.notes_text.pack(fill="x")

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Save Assessment Changes", command=self.save_assessment_changes).pack(side="right")
        ttk.Button(button_frame, text="Export to Excel", command=self.export_selected_clinic_to_excel).pack(side="right", padx=(0, 8))

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def reposition_all_dropdowns(self):
        if self.clinic_combobox is not None:
            self.clinic_combobox.reposition_dropdown()

    def on_canvas_scroll(self, *args):
        self.canvas.yview(*args)
        self.reposition_all_dropdowns()

    def open_combobox_dropdown(self, event):
        widget = event.widget
        widget.after_idle(lambda: widget.event_generate("<Down>"))

    def refresh_data(self):
        current_clinic = self.selected_clinic_var.get().strip()
        current_assessment = self.selected_assessment_var.get().strip()

        self.load_clinic_names()

        clinic_names = list(self.clinic_combobox.all_values)
        if current_clinic and current_clinic in clinic_names:
            self.selected_clinic_var.set(current_clinic)
            self.on_clinic_selected()

        assessment_values = list(self.assessment_combobox["values"])
        if current_assessment and current_assessment in assessment_values:
            self.selected_assessment_var.set(current_assessment)
            self.on_assessment_selected()
        else:
            self.clear_details()

    def load_clinic_names(self):
        clinic_names = get_clinic_names()
        self.clinic_combobox.set_values(clinic_names)

    def on_clinic_selected(self):
        clinic_name = self.selected_clinic_var.get().strip()
        if not clinic_name:
            self.clear_details()
            return

        self.current_name_var.set(clinic_name)
        self.load_assessment_records(clinic_name)

        latest = get_latest_assessment_for_clinic(clinic_name)
        if latest:
            self.current_date_var.set(latest[2])
        else:
            self.current_date_var.set("—")

    def load_assessment_records(self, clinic_name):
        rows = get_assessments_for_clinic(clinic_name)
        self.assessment_map = {}
        display_values = []
        for assessment_id, assessment_date in rows:
            label = f"{assessment_date} (ID: {assessment_id})"
            self.assessment_map[label] = assessment_id
            display_values.append(label)

        self.assessment_combobox["values"] = display_values

        if display_values:
            self.selected_assessment_var.set(display_values[0])
            self.on_assessment_selected()
        else:
            self.selected_assessment_var.set("")
            self.clear_assessment_display()

    def on_assessment_selected(self):
        selected_label = self.selected_assessment_var.get().strip()
        if not selected_label:
            self.clear_assessment_display()
            return

        assessment_id = self.assessment_map.get(selected_label)
        if not assessment_id:
            self.clear_assessment_display()
            return

        detail = get_assessment_detail(assessment_id)
        if not detail:
            self.clear_assessment_display()
            return

        self.current_assessment_id = assessment_id
        self.current_date_var.set(detail.get("assessment_date") or "—")
        self.current_name_var.set(detail.get("clinic_name") or "—")
        self.current_region_var.set(detail.get("region") or "—")
        self.current_specialty_var.set(detail.get("specialty") or "—")

        tests_text = (detail.get("tests_performed") or "").strip()
        selected_tests = {item.strip() for item in tests_text.split(",") if item.strip()}
        for test_name, var in self.tests_vars.items():
            var.set(test_name in selected_tests)

        for item in ASSESSMENT_ITEMS:
            number = item["number"]
            idx = number - 1

            self.answer_vars[idx].set(detail.get(f"q{number}_answer") or "")

            template_comment = detail.get(f"q{number}_template_comment")
            manual_comment = detail.get(f"q{number}_manual_comment")
            custom_comment = detail.get(f"q{number}_custom_comment")
            combined_comment = detail.get(f"q{number}_comment")

            if template_comment:
                selected_templates = [part.strip() for part in template_comment.split("\n") if part.strip()]
            else:
                selected_templates = []

            # Manual Comments doubles as the Custom Comments value used in
            # the Excel export. Fall back to older saved fields so existing
            # records still display correctly.
            if not manual_comment:
                manual_comment = custom_comment or (combined_comment if not template_comment else "")

            self.question_selected_templates[idx] = selected_templates
            self.refresh_template_preview(idx)

            self.manual_comment_widgets[idx].delete("1.0", tk.END)
            self.manual_comment_widgets[idx].insert("1.0", manual_comment or "")

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", detail.get("notes") or "")

    def edit_clinic_name(self):
        old_name = self.current_name_var.get().strip()
        if not old_name or old_name == "—":
            messagebox.showerror("No Clinic Selected", "Please select a clinic first.")
            return

        popup_values = get_clinic_names()

        def apply_name(new_name):
            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("Validation Error", "Clinic name cannot be blank.")
                return
            if new_name == old_name:
                return

            updated_count = rename_clinic(old_name, new_name)
            if updated_count <= 0:
                messagebox.showwarning("No Changes", "No clinic records were updated.")
                return

            self.load_clinic_names()
            self.selected_clinic_var.set(new_name)
            self.current_name_var.set(new_name)
            self.on_clinic_selected()
            messagebox.showinfo("Clinic Updated", f"Clinic name updated successfully.\n\nRows updated: {updated_count}")

        SelectionEditPopup(
            self,
            title="Edit Clinic Name",
            prompt="Select an existing clinic name or type a new one:",
            values=popup_values,
            initial_value=old_name,
            on_apply=apply_name,
            allow_typing=True,
        )

    def edit_region(self):
        if not self.current_assessment_id:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        current_region = self.current_region_var.get().strip()

        def apply_region(new_region):
            new_region = normalize_choice(new_region, REGION_OPTIONS)
            if not new_region:
                messagebox.showerror("Validation Error", "Region cannot be blank.")
                return

            updated_count = update_assessment_region(self.current_assessment_id, new_region)
            if updated_count <= 0:
                messagebox.showwarning("No Changes", "No region was updated.")
                return

            self.current_region_var.set(new_region)
            self.on_assessment_selected()
            messagebox.showinfo("Region Updated", "Assessment region updated successfully.")

        SelectionEditPopup(
            self,
            title="Edit Region",
            prompt="Select or enter the region for this assessment:",
            values=REGION_OPTIONS,
            initial_value=current_region,
            on_apply=apply_region,
            allow_typing=True,
        )

    def edit_specialty(self):
        if not self.current_assessment_id:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        current_specialty = self.current_specialty_var.get().strip()

        def apply_specialty(new_specialty):
            new_specialty = normalize_choice(new_specialty, SPECIALTY_OPTIONS)
            if not new_specialty:
                messagebox.showerror("Validation Error", "Specialty cannot be blank.")
                return

            updated_count = update_assessment_specialty(self.current_assessment_id, new_specialty)
            if updated_count <= 0:
                messagebox.showwarning("No Changes", "No specialty was updated.")
                return

            self.current_specialty_var.set(new_specialty)
            self.on_assessment_selected()
            messagebox.showinfo("Specialty Updated", "Assessment specialty updated successfully.")

        SelectionEditPopup(
            self,
            title="Edit Specialty",
            prompt="Select or enter the specialty for this assessment:",
            values=SPECIALTY_OPTIONS,
            initial_value=current_specialty,
            on_apply=apply_specialty,
            allow_typing=True,
        )

    def edit_assessment_date(self):
        selected_label = self.selected_assessment_var.get().strip()
        if not selected_label:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        assessment_id = self.assessment_map.get(selected_label)
        if not assessment_id:
            messagebox.showerror("Selection Error", "Could not identify the selected assessment.")
            return

        current_date = self.current_date_var.get().strip()

        popup = SelectionEditPopup(
            self,
            title="Edit Assessment Date",
            prompt="Enter the new assessment date (YYYY-MM-DD):",
            values=[],
            initial_value=current_date,
            on_apply=lambda new_date: self.apply_assessment_date_update(assessment_id, new_date),
            allow_typing=True,
        )
        if isinstance(popup.combo, SearchableCombobox):
            popup.combo.set_values([])

    def apply_assessment_date_update(self, assessment_id, new_date):
        new_date = new_date.strip()
        if not new_date:
            messagebox.showerror("Validation Error", "Assessment date cannot be blank.")
            return
        if not is_valid_date(new_date):
            messagebox.showerror("Validation Error", "Assessment date must be in YYYY-MM-DD format.")
            return

        updated_count = update_assessment_date(assessment_id, new_date)
        if updated_count <= 0:
            messagebox.showwarning("No Changes", "No assessment date was updated.")
            return

        clinic_name = self.selected_clinic_var.get().strip()
        self.load_assessment_records(clinic_name)

        refreshed_label = f"{new_date} (ID: {assessment_id})"
        if refreshed_label in self.assessment_map:
            self.selected_assessment_var.set(refreshed_label)
            self.on_assessment_selected()

        messagebox.showinfo("Assessment Updated", "Assessment date updated successfully.")

    def delete_selected_assessment(self):
        selected_label = self.selected_assessment_var.get().strip()
        if not selected_label:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        assessment_id = self.assessment_map.get(selected_label)
        if not assessment_id:
            messagebox.showerror("Selection Error", "Could not identify the selected assessment.")
            return

        detail = get_assessment_detail(assessment_id)
        if not detail:
            messagebox.showerror("Not Found", "The selected assessment could not be found.")
            return

        clinic_name = (detail.get("clinic_name") or "").strip()
        assessment_date = detail.get("assessment_date") or ""

        confirmed = messagebox.askyesno(
            "Delete Assessment",
            f"Are you sure you want to delete this assessment?\n\nClinic: {clinic_name}\nDate: {assessment_date}\nID: {assessment_id}\n\nThis cannot be undone.",
        )
        if not confirmed:
            return

        deleted_count = delete_assessment(assessment_id)
        if deleted_count <= 0:
            messagebox.showwarning("Delete Failed", "No assessment was deleted.")
            return

        remaining = get_assessments_for_clinic(clinic_name)
        if remaining:
            self.load_assessment_records(clinic_name)
            self.selected_clinic_var.set(clinic_name)
            self.current_name_var.set(clinic_name)
        else:
            self.selected_clinic_var.set("")
            self.load_clinic_names()
            self.clear_details()

        messagebox.showinfo("Assessment Deleted", "The selected assessment was deleted successfully.")

    def open_question_template_popup(self, index):
        templates = self.question_template_options[index]
        selected = self.question_selected_templates[index]
        QuestionTemplatePopup(self, f"Question {index + 1} Templates", templates, selected, lambda new_selected, idx=index: self.apply_question_templates(idx, new_selected))

    def apply_question_templates(self, index, selected_templates):
        self.question_selected_templates[index] = selected_templates
        self.refresh_template_preview(index)

    def refresh_template_preview(self, index):
        preview = self.template_preview_widgets[index]
        preview.configure(state="normal")
        preview.delete("1.0", tk.END)
        preview.insert("1.0", "\n".join(self.question_selected_templates[index]))
        preview.configure(state="disabled")

    def build_question_template_comment(self, index):
        text = "\n".join(self.question_selected_templates[index]).strip()
        return text or None

    def build_question_manual_comment(self, index):
        text = self.manual_comment_widgets[index].get("1.0", tk.END).strip()
        return text or None

    def build_question_comment(self, index):
        # The general "Comments" column in the Excel export is built from
        # the template comment only. Manual Comments are the Custom
        # Comments and are shown in their own column (see save logic below).
        template_part = self.build_question_template_comment(index)
        return template_part or None

    def save_assessment_changes(self):
        selected_label = self.selected_assessment_var.get().strip()
        if not selected_label:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        assessment_id = self.assessment_map.get(selected_label)
        if not assessment_id:
            messagebox.showerror("Selection Error", "Could not identify the selected assessment.")
            return

        tests_selected = [name for name, var in self.tests_vars.items() if var.get()]
        tests_performed = ", ".join(tests_selected)

        answers_and_comments = []
        for index in range(len(ASSESSMENT_ITEMS)):
            answer = self.answer_vars[index].get().strip() or None
            template_comment = self.build_question_template_comment(index)
            manual_comment = self.build_question_manual_comment(index)
            combined_comment = self.build_question_comment(index)
            answers_and_comments.append({
                "answer": answer,
                "combined_comment": combined_comment,
                "template_comment": template_comment,
                "manual_comment": manual_comment,
                # Manual Comments and Custom Comments are the same field;
                # save the same text to both columns.
                "custom_comment": manual_comment,
            })

        notes = self.notes_text.get("1.0", tk.END).strip()

        updated_count = update_assessment_content(
            assessment_id=assessment_id,
            tests_performed=tests_performed,
            notes=notes,
            answers_and_comments=answers_and_comments,
        )
        if updated_count <= 0:
            messagebox.showwarning("No Changes", "No assessment content was updated.")
            return

        self.on_assessment_selected()
        messagebox.showinfo("Saved", "Assessment details updated successfully.")

    def export_selected_clinic_to_excel(self):
        clinic_name = self.selected_clinic_var.get().strip()
        if not clinic_name:
            messagebox.showerror("No Clinic Selected", "Please select a clinic first.")
            return

        selected_label = self.selected_assessment_var.get().strip()
        if not selected_label:
            messagebox.showerror("No Assessment Selected", "Please select an assessment record first.")
            return

        assessment_id = self.assessment_map.get(selected_label)
        if not assessment_id:
            messagebox.showerror("Selection Error", "Could not identify the selected assessment.")
            return

        selected_detail = get_assessment_detail(assessment_id)
        if not selected_detail:
            messagebox.showerror("No Data", "Could not load the selected assessment.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Clinic Export",
            defaultextension=".xlsx",
            initialfile=f"{clinic_name}_clinic_checklist.xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not file_path:
            return

        try:
            export_clinic_workbook(
                file_path=file_path,
                selected_detail=selected_detail,
                assessment_items=ASSESSMENT_ITEMS,
                clinic_name=clinic_name,
                sheet_title="Clinic Checklist",
            )
            messagebox.showinfo("Export Complete", f"Clinic export saved successfully.\n\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export clinic workbook.\n\n{e}")

    def clear_assessment_display(self):
        self.current_assessment_id = None
        self.current_date_var.set("—")
        self.current_region_var.set("—")
        self.current_specialty_var.set("—")

        for test_name, var in self.tests_vars.items():
            var.set(False)

        for answer_var in self.answer_vars:
            answer_var.set("")

        for idx, preview_widget in enumerate(self.template_preview_widgets):
            self.question_selected_templates[idx] = []
            preview_widget.configure(state="normal")
            preview_widget.delete("1.0", tk.END)
            preview_widget.configure(state="disabled")

        for comment_widget in self.manual_comment_widgets:
            comment_widget.delete("1.0", tk.END)

        self.notes_text.delete("1.0", tk.END)

    def clear_details(self):
        self.current_name_var.set("—")
        self.current_region_var.set("—")
        self.current_specialty_var.set("—")
        self.current_date_var.set("—")
        self.selected_assessment_var.set("")
        self.assessment_combobox["values"] = []
        self.assessment_map = {}
        self.clear_assessment_display()