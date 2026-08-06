import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from ..db import (
    get_clinic_names,
    get_all_question_comment_templates,
    get_latest_region_for_clinic,
    get_latest_specialty_for_clinic,
    get_assessments_for_clinic,
    update_assessment_content,
    update_assessment_region,
    update_assessment_specialty,
    create_assessment,
)
from ..validators import is_valid_date, normalize_choice
from .assessment_config import (
    TESTS_PERFORMED,
    ANSWER_OPTIONS,
    ASSESSMENT_ITEMS,
    SPECIALTY_OPTIONS,
    REGION_OPTIONS,
)
from .scroll_utils import bind_mousewheel_scrolling
from .widgets import SearchableCombobox, QuestionTemplatePopup


class NewAssessment(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.clinic_name_var = tk.StringVar()
        self.region_var = tk.StringVar()
        self.specialty_var = tk.StringVar()
        self.assessment_date_var = tk.StringVar(value=date.today().isoformat())

        self.answer_vars = []
        self.manual_comment_widgets = []
        self.question_selected_templates = [[] for _ in range(len(ASSESSMENT_ITEMS))]
        self.question_template_options = []
        self.question_preview_widgets = []
        self.description_labels = []
        self.category_labels = []

        self.tests_performed_vars = {}

        self.all_clinic_names = []
        self.all_region_options = list(REGION_OPTIONS)
        self.all_specialty_options = list(SPECIALTY_OPTIONS)

        self.clinic_search = None
        self.region_search = None
        self.specialty_search = None
        self.canvas = None
        self.canvas_window = None
        self.page_frame = None

        self.overall_manual_text = None

        self.build_ui()
        self.load_clinic_names()

    def build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.on_canvas_scroll)
        self.page_frame = ttk.Frame(self.canvas)

        self.page_frame.bind("<Configure>", self.on_scrollable_frame_configure)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.page_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bind_mousewheel_scrolling(self.canvas)
        # The custom combobox dropdowns below float in their own Toplevel,
        # so they need to be repositioned (or hidden) whenever the canvas
        # scrolls - on top of the shared scroll handler's own binding.
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(sequence, lambda e: self.reposition_all_dropdowns(), add="+")

        top_frame = ttk.Frame(self.page_frame, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Clinic Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.clinic_search = SearchableCombobox(
            top_frame,
            textvariable=self.clinic_name_var,
            values=self.all_clinic_names,
            width=30,
            on_select=self.on_clinic_selected,
            on_focus_out=self.try_fill_fields_from_clinic,
            scroll_canvas=self.canvas,
        )
        self.clinic_search.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(top_frame, text="Region:").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.region_search = SearchableCombobox(
            top_frame,
            textvariable=self.region_var,
            values=self.all_region_options,
            width=22,
            scroll_canvas=self.canvas,
        )
        self.region_search.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(top_frame, text="Specialty:").grid(row=0, column=4, padx=5, pady=5, sticky="w")

        self.specialty_search = SearchableCombobox(
            top_frame,
            textvariable=self.specialty_var,
            values=self.all_specialty_options,
            width=30,
            scroll_canvas=self.canvas,
        )
        self.specialty_search.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(top_frame, text="Assessment Date (YYYY-MM-DD):").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        ttk.Entry(top_frame, textvariable=self.assessment_date_var, width=20).grid(row=0, column=7, padx=5, pady=5, sticky="w")
        ttk.Button(top_frame, text="Use Today", command=self.set_today).grid(row=0, column=8, padx=5, pady=5, sticky="w")

        top_frame.columnconfigure(1, weight=2)
        top_frame.columnconfigure(3, weight=1)
        top_frame.columnconfigure(5, weight=2)

        tests_frame = ttk.LabelFrame(self.page_frame, text="Tests Performed", padding=(10, 8))
        tests_frame.pack(fill="x", padx=10, pady=(0, 10))

        cols = 3
        for i, test_name in enumerate(TESTS_PERFORMED):
            var = tk.BooleanVar(value=False)
            self.tests_performed_vars[test_name] = var
            row = i // cols
            col = i % cols
            ttk.Checkbutton(
                tests_frame,
                text=test_name,
                variable=var
            ).grid(row=row, column=col, sticky="w", padx=5, pady=2)

        for c in range(cols):
            tests_frame.columnconfigure(c, weight=1)

        questions_frame = ttk.Frame(self.page_frame, padding=(10, 0, 10, 10))
        questions_frame.pack(fill="x")

        ttk.Label(questions_frame, text="Item", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Category", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Description", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Answer", font=("Segoe UI", 10, "bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Templates", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Selected Templates", font=("Segoe UI", 10, "bold")).grid(row=0, column=5, padx=5, pady=5, sticky="w")
        ttk.Label(questions_frame, text="Manual Comment", font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=5, pady=5, sticky="w")

        questions_frame.columnconfigure(0, weight=0, minsize=40)
        questions_frame.columnconfigure(1, weight=1, minsize=120)
        questions_frame.columnconfigure(2, weight=3, minsize=250)
        questions_frame.columnconfigure(3, weight=1, minsize=90)
        questions_frame.columnconfigure(4, weight=1, minsize=150)
        questions_frame.columnconfigure(5, weight=3, minsize=320)
        questions_frame.columnconfigure(6, weight=3, minsize=260)

        db_templates_by_question = get_all_question_comment_templates()

        for row_index, item in enumerate(ASSESSMENT_ITEMS, start=1):
            ttk.Label(questions_frame, text=str(item["number"])).grid(row=row_index, column=0, padx=5, pady=4, sticky="nw")

            category_label = ttk.Label(
                questions_frame,
                text=item["category"],
                wraplength=140,
                justify="left"
            )
            category_label.grid(row=row_index, column=1, padx=5, pady=4, sticky="nsew")
            self.category_labels.append(category_label)

            description_label = ttk.Label(
                questions_frame,
                text=item["text"],
                wraplength=300,
                justify="left"
            )
            description_label.grid(row=row_index, column=2, padx=5, pady=4, sticky="nsew")
            self.description_labels.append(description_label)

            answer_var = tk.StringVar(value="")
            self.answer_vars.append(answer_var)

            answer_frame = ttk.Frame(questions_frame)
            answer_frame.grid(row=row_index, column=3, padx=5, pady=4, sticky="nw")

            for option in ANSWER_OPTIONS:
                ttk.Radiobutton(
                    answer_frame,
                    text=option,
                    variable=answer_var,
                    value=option
                ).pack(anchor="w")

            default_templates = item.get("templates", []) or []
            saved_templates = db_templates_by_question.get(item["number"], [])
            all_templates = list(dict.fromkeys(default_templates + saved_templates))
            self.question_template_options.append(all_templates)

            template_frame = ttk.Frame(questions_frame)
            template_frame.grid(row=row_index, column=4, padx=5, pady=4, sticky="nsew")

            ttk.Button(
                template_frame,
                text="Select Comments",
                command=lambda idx=row_index - 1: self.open_question_template_popup(idx)
            ).pack(anchor="w", fill="x")

            ttk.Label(
                template_frame,
                text="Click to view full comments",
                foreground="gray"
            ).pack(anchor="w", pady=(4, 0))

            preview_text = tk.Text(questions_frame, height=5, width=50, wrap="word")
            preview_text.grid(row=row_index, column=5, padx=5, pady=4, sticky="nsew")
            preview_text.configure(state="disabled")
            self.question_preview_widgets.append(preview_text)

            manual_text = tk.Text(questions_frame, height=5, width=45, wrap="word")
            manual_text.grid(row=row_index, column=6, padx=5, pady=4, sticky="nsew")
            self.manual_comment_widgets.append(manual_text)

        notes_frame = ttk.Frame(self.page_frame, padding=10)
        notes_frame.pack(fill="x")

        ttk.Label(notes_frame, text="Overall Comment:").grid(row=0, column=0, padx=5, pady=5, sticky="nw")

        self.overall_manual_text = tk.Text(notes_frame, height=8, width=90, wrap="word")
        self.overall_manual_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        notes_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.page_frame, padding=10)
        button_frame.pack(fill="x")

        ttk.Button(
            button_frame,
            text="Save Assessment",
            command=self.save_assessment
        ).pack(anchor="e")

    def reposition_all_dropdowns(self):
        for widget in (self.clinic_search, self.region_search, self.specialty_search):
            if widget is not None:
                widget.reposition_dropdown()

    def on_canvas_scroll(self, *args):
        self.canvas.yview(*args)
        self.reposition_all_dropdowns()

    def refresh_data(self):
        self.load_clinic_names()
        self.refresh_comment_template_lists()

    def set_today(self):
        self.assessment_date_var.set(date.today().isoformat())

    def load_clinic_names(self):
        self.all_clinic_names = get_clinic_names()
        if self.clinic_search:
            self.clinic_search.set_values(self.all_clinic_names)

    def refresh_comment_template_lists(self):
        db_templates_by_question = get_all_question_comment_templates()
        self.question_template_options = []
        for item in ASSESSMENT_ITEMS:
            default_templates = item.get("templates", []) or []
            db_templates = db_templates_by_question.get(item["number"], [])
            all_templates = list(dict.fromkeys(default_templates + db_templates))
            self.question_template_options.append(all_templates)

    def on_clinic_selected(self):
        clinic_name = self.clinic_name_var.get().strip()
        if not clinic_name:
            return

        latest_region = get_latest_region_for_clinic(clinic_name)
        if latest_region:
            self.region_search.set(latest_region)

        latest_specialty = get_latest_specialty_for_clinic(clinic_name)
        if latest_specialty:
            self.specialty_search.set(latest_specialty)

    def try_fill_fields_from_clinic(self):
        clinic_name = self.clinic_name_var.get().strip()
        if not clinic_name:
            return

        latest_region = get_latest_region_for_clinic(clinic_name)
        if latest_region and not self.region_var.get().strip():
            self.region_search.set(latest_region)

        latest_specialty = get_latest_specialty_for_clinic(clinic_name)
        if latest_specialty and not self.specialty_var.get().strip():
            self.specialty_search.set(latest_specialty)

    def open_question_template_popup(self, index):
        templates = self.question_template_options[index]
        selected = self.question_selected_templates[index][:]

        QuestionTemplatePopup(
            self,
            f"Question {index + 1} Templates",
            templates,
            selected,
            lambda new_selected, idx=index: self.apply_question_templates(idx, new_selected)
        )

    def apply_question_templates(self, index, selected_templates):
        self.question_selected_templates[index] = selected_templates
        self.refresh_question_preview(index)

    def refresh_question_preview(self, index):
        preview = self.question_preview_widgets[index]
        preview.configure(state="normal")
        preview.delete("1.0", tk.END)
        preview.insert("1.0", "\n\n".join(self.question_selected_templates[index]))
        preview.configure(state="disabled")

    def build_question_template_comment(self, index):
        text = "\n".join(self.question_selected_templates[index]).strip()
        return text or None

    def build_question_manual_comment(self, index):
        text = self.manual_comment_widgets[index].get("1.0", "end").strip()
        return text or None

    def build_question_comment(self, index):
        # The "Comments" column in the Excel export is built from the
        # template comment only. Manual comments are the Custom Comments
        # and are saved to their own column (see save_assessment below).
        template_part = self.build_question_template_comment(index)
        return template_part or None

    def build_overall_comment(self):
        return self.overall_manual_text.get("1.0", "end").strip()

    def find_assessment_id_for_date(self, clinic_name, assessment_date):
        for assessment_id, existing_date in get_assessments_for_clinic(clinic_name):
            if existing_date == assessment_date:
                return assessment_id
        return None

    def save_assessment(self):
        clinic_name = self.clinic_name_var.get().strip()
        region = normalize_choice(self.region_var.get(), self.all_region_options)
        specialty = normalize_choice(self.specialty_var.get(), self.all_specialty_options)
        assessment_date = self.assessment_date_var.get().strip()
        notes = self.build_overall_comment()

        if not clinic_name:
            messagebox.showerror("Validation Error", "Please select or enter a clinic name.")
            return

        if not region:
            messagebox.showerror("Validation Error", "Please select or enter a region.")
            return

        if not specialty:
            messagebox.showerror("Validation Error", "Please select or enter a specialty.")
            return

        if not assessment_date:
            messagebox.showerror("Validation Error", "Please select an assessment date.")
            return

        if not is_valid_date(assessment_date):
            messagebox.showerror("Validation Error", "Assessment date must be in YYYY-MM-DD format.")
            return

        tests_selected = [name for name, var in self.tests_performed_vars.items() if var.get()]
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

        # A clinic + date combination that already has a record is an
        # update to that assessment; otherwise this date becomes a new
        # assessment instance for the clinic.
        existing_id = self.find_assessment_id_for_date(clinic_name, assessment_date)

        try:
            if existing_id:
                confirmed = messagebox.askyesno(
                    "Assessment Exists",
                    f"An assessment for {clinic_name} on {assessment_date} already "
                    "exists.\n\nSaving will overwrite it. Continue?",
                )
                if not confirmed:
                    return
                update_assessment_content(
                    assessment_id=existing_id,
                    tests_performed=tests_performed,
                    notes=notes,
                    answers_and_comments=answers_and_comments,
                )
                update_assessment_region(existing_id, region)
                update_assessment_specialty(existing_id, specialty)
                messagebox.showinfo("Saved", "Assessment updated successfully.")
            else:
                create_assessment(
                    clinic_name=clinic_name,
                    assessment_date=assessment_date,
                    region=region,
                    specialty=specialty,
                    tests_performed=tests_performed,
                    notes=notes,
                    answers_and_comments=answers_and_comments,
                )
                messagebox.showinfo("Saved", "Assessment saved successfully.")

            self.load_clinic_names()
            self.clear_form()

        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save assessment.\n\n{e}")

    def clear_form(self):
        self.clinic_name_var.set("")
        self.region_var.set("")
        self.specialty_var.set("")
        self.assessment_date_var.set(date.today().isoformat())

        for var in self.answer_vars:
            var.set("")

        for selected in self.question_selected_templates:
            selected.clear()

        for preview in self.question_preview_widgets:
            preview.configure(state="normal")
            preview.delete("1.0", tk.END)
            preview.configure(state="disabled")

        for widget in self.manual_comment_widgets:
            widget.delete("1.0", tk.END)

        for var in self.tests_performed_vars.values():
            var.set(False)

        self.overall_manual_text.delete("1.0", tk.END)

    def on_scrollable_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.reposition_all_dropdowns()

    def on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self.update_responsive_layout(event.width)
        self.reposition_all_dropdowns()

    def update_responsive_layout(self, width):
        if width < 1100:
            category_wrap = 120
            description_wrap = 220
            preview_width = 32
            manual_width = 30
        elif width < 1500:
            category_wrap = 150
            description_wrap = 320
            preview_width = 42
            manual_width = 40
        else:
            category_wrap = 220
            description_wrap = 520
            preview_width = 58
            manual_width = 60

        for label in self.category_labels:
            label.configure(wraplength=category_wrap)

        for label in self.description_labels:
            label.configure(wraplength=description_wrap)

        for preview in self.question_preview_widgets:
            preview.configure(width=preview_width)

        for text_widget in self.manual_comment_widgets:
            text_widget.configure(width=manual_width)
