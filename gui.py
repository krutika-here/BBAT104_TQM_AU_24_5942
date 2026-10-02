"""
Tkinter GUI Frontend for Online Quiz System.
Course: BBAT104 - Fundamentals of Total Quality Management
Roll No / Reg: AU-24-5942
"""

import tkinter as tk
from tkinter import ttk, messagebox
import database

class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Online Quiz System - BBAT104 (AU-24-5942)")
        self.geometry("980x700")
        self.minsize(850, 600)

        # Style configuration
        self.configure(bg="#F1F5F9")
        self.setup_styles()

        # Navigation header
        self.create_header()

        # Container for swappable screens
        self.container = ttk.Frame(self, style="Content.TFrame")
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Active state for quiz taking
        self.current_quiz = None
        self.current_questions = []
        self.current_q_index = 0
        self.user_answers = {}
        self.student_name = ""
        self.student_roll = ""
        self.remaining_seconds = 0
        self.timer_after_id = None

        # Show default home screen
        self.show_home_screen()

    def setup_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Colors
        PRIMARY = "#1E40AF"      # Deep Blue
        SECONDARY = "#2563EB"    # Blue Accent
        SUCCESS = "#16A34A"      # Green
        DANGER = "#DC2626"       # Red
        BG = "#F8FAFC"           # Slate 50
        CARD_BG = "#FFFFFF"

        self.style.configure(".", background=BG, font=("Helvetica", 10))
        self.style.configure("Content.TFrame", background=BG)
        self.style.configure("Card.TFrame", background=CARD_BG, relief="ridge", borderwidth=1)

        # Header Styles
        self.style.configure("Header.TFrame", background=PRIMARY)
        self.style.configure("HeaderTitle.TLabel", background=PRIMARY, foreground="#FFFFFF", font=("Helvetica", 16, "bold"))
        self.style.configure("HeaderSub.TLabel", background=PRIMARY, foreground="#DBEAFE", font=("Helvetica", 10))

        # Nav Buttons
        self.style.configure("Nav.TButton", font=("Helvetica", 10, "bold"), padding=6)
        
        # Action Buttons
        self.style.configure("Primary.TButton", font=("Helvetica", 10, "bold"), foreground="#FFFFFF", background=PRIMARY, padding=6)
        self.style.configure("Success.TButton", font=("Helvetica", 10, "bold"), foreground="#FFFFFF", background=SUCCESS, padding=6)
        self.style.configure("Danger.TButton", font=("Helvetica", 10, "bold"), foreground="#FFFFFF", background=DANGER, padding=6)

        # Labels
        self.style.configure("Title.TLabel", font=("Helvetica", 15, "bold"), background=BG, foreground="#0F172A")
        self.style.configure("SubTitle.TLabel", font=("Helvetica", 11), background=BG, foreground="#475569")
        self.style.configure("CardLabel.TLabel", font=("Helvetica", 10, "bold"), background=CARD_BG, foreground="#1E293B")
        self.style.configure("QuestionText.TLabel", font=("Helvetica", 13, "bold"), background=CARD_BG, foreground="#0F172A", wraplength=700)
        self.style.configure("Timer.TLabel", font=("Helvetica", 12, "bold"), background=CARD_BG, foreground=DANGER)

        # Treeview styling
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview", rowheight=26)

    def create_header(self):
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(20, 12))
        header_frame.pack(fill=tk.X)

        title_box = ttk.Frame(header_frame, style="Header.TFrame")
        title_box.pack(side=tk.LEFT)

        title_lbl = ttk.Label(title_box, text="Online Quiz System", style="HeaderTitle.TLabel")
        title_lbl.pack(anchor="w")

        sub_lbl = ttk.Label(title_box, text="BBAT104: Fundamentals of TQM | Reg. AU-24-5942", style="HeaderSub.TLabel")
        sub_lbl.pack(anchor="w")

        # Nav button bar
        nav_bar = ttk.Frame(header_frame, style="Header.TFrame")
        nav_bar.pack(side=tk.RIGHT)

        ttk.Button(nav_bar, text="Take Quiz", style="Nav.TButton", command=self.show_home_screen).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav_bar, text="Manage Quizzes", style="Nav.TButton", command=self.show_admin_screen).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav_bar, text="Student Results", style="Nav.TButton", command=self.show_results_screen).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav_bar, text="TQM Quality Logs", style="Nav.TButton", command=self.show_tqm_logs_screen).pack(side=tk.LEFT, padx=4)

    def clear_container(self):
        if self.timer_after_id:
            self.after_cancel(self.timer_after_id)
            self.timer_after_id = None
        for widget in self.container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------
    # SCREEN 1: Home / Student Quiz Portal
    # -------------------------------------------------------------
    def show_home_screen(self):
        self.clear_container()

        title_label = ttk.Label(self.container, text="Student Quiz Portal", style="Title.TLabel")
        title_label.pack(anchor="w", pady=(0, 5))

        desc_label = ttk.Label(self.container, text="Enter your details, select a quiz, and start your automated test.", style="SubTitle.TLabel")
        desc_label.pack(anchor="w", pady=(0, 15))

        card = ttk.Frame(self.container, style="Card.TFrame", padding=25)
        card.pack(fill=tk.BOTH, expand=True)

        form_frame = ttk.Frame(card, style="Card.TFrame")
        form_frame.pack(fill=tk.X, pady=10)

        # Student Name
        ttk.Label(form_frame, text="Student Full Name *:", style="CardLabel.TLabel").grid(row=0, column=0, sticky="w", pady=8, padx=10)
        self.entry_name = ttk.Entry(form_frame, width=35, font=("Helvetica", 11))
        self.entry_name.grid(row=0, column=1, sticky="w", pady=8, padx=10)
        self.entry_name.insert(0, "Krutika Agrawal")

        # Roll Number (Poka-Yoke check)
        ttk.Label(form_frame, text="Roll / Reg. Number *:", style="CardLabel.TLabel").grid(row=1, column=0, sticky="w", pady=8, padx=10)
        self.entry_roll = ttk.Entry(form_frame, width=35, font=("Helvetica", 11))
        self.entry_roll.grid(row=1, column=1, sticky="w", pady=8, padx=10)
        self.entry_roll.insert(0, "AU-24-5942")

        # Select Quiz
        ttk.Label(form_frame, text="Select Quiz Topic *:", style="CardLabel.TLabel").grid(row=2, column=0, sticky="w", pady=8, padx=10)
        self.quizzes_data = database.get_all_quizzes()
        
        quiz_options = [f"{q['id']} - {q['title']} ({q['question_count']} questions, {q['time_limit_mins']} mins)" for q in self.quizzes_data]
        self.quiz_combo = ttk.Combobox(form_frame, values=quiz_options, width=45, state="readonly", font=("Helvetica", 10))
        if quiz_options:
            self.quiz_combo.current(0)
        self.quiz_combo.grid(row=2, column=1, sticky="w", pady=8, padx=10)

        # Quiz details description card
        self.lbl_quiz_info = ttk.Label(card, text="", style="Card.TFrame", font=("Helvetica", 10, "italic"), foreground="#475569")
        self.lbl_quiz_info.pack(fill=tk.X, padx=10, pady=10)

        def on_quiz_change(event=None):
            idx = self.quiz_combo.current()
            if idx >= 0 and idx < len(self.quizzes_data):
                q = self.quizzes_data[idx]
                self.lbl_quiz_info.config(text=f"Quiz Overview: {q['description']} | Pass Mark: {q['pass_percentage']}%")

        self.quiz_combo.bind("<<ComboboxSelected>>", on_quiz_change)
        on_quiz_change()

        # Start button
        btn_start = ttk.Button(card, text="Start Quiz Now ➔", style="Success.TButton", command=self.validate_and_start_quiz)
        btn_start.pack(anchor="w", padx=10, pady=20)

    def validate_and_start_quiz(self):
        name = self.entry_name.get().strip()
        roll = self.entry_roll.get().strip()

        # Poka-Yoke error prevention check
        if not name:
            messagebox.showwarning("Input Required (Poka-Yoke)", "Please enter your Full Name to proceed.")
            database.log_defect("Input Validation", "User attempted quiz start without name", "Low", "Resolved")
            return
        if not roll:
            messagebox.showwarning("Input Required (Poka-Yoke)", "Please enter your Roll/Registration Number.")
            database.log_defect("Input Validation", "User attempted quiz start without roll number", "Low", "Resolved")
            return

        idx = self.quiz_combo.current()
        if idx < 0:
            messagebox.showwarning("Selection Required", "Please select a quiz.")
            return

        selected_quiz = self.quizzes_data[idx]
        questions = database.get_questions_by_quiz(selected_quiz["id"])

        if not questions:
            messagebox.showerror("No Questions", "This quiz does not have any questions yet. Please add questions in the Admin panel.")
            return

        self.student_name = name
        self.student_roll = roll
        self.current_quiz = selected_quiz
        self.current_questions = questions
        self.current_q_index = 0
        self.user_answers = {}
        self.remaining_seconds = int(selected_quiz["time_limit_mins"]) * 60

        self.show_quiz_taking_screen()

    # -------------------------------------------------------------
    # SCREEN 2: Quiz Taking Engine with Timer
    # -------------------------------------------------------------
    def show_quiz_taking_screen(self):
        self.clear_container()

        # Top Bar: Quiz Title & Countdown Timer
        top_bar = ttk.Frame(self.container, style="Content.TFrame")
        top_bar.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ttk.Label(top_bar, text=self.current_quiz["title"], style="Title.TLabel")
        title_lbl.pack(side=tk.LEFT)

        self.lbl_timer = ttk.Label(top_bar, text="", style="Timer.TLabel")
        self.lbl_timer.pack(side=tk.RIGHT)
        self.update_timer_display()
        self.start_timer_tick()

        # Card container for question
        self.q_card = ttk.Frame(self.container, style="Card.TFrame", padding=20)
        self.q_card.pack(fill=tk.BOTH, expand=True)

        self.lbl_q_num = ttk.Label(self.q_card, text="", style="CardLabel.TLabel")
        self.lbl_q_num.pack(anchor="w", pady=(0, 5))

        self.lbl_q_text = ttk.Label(self.q_card, text="", style="QuestionText.TLabel")
        self.lbl_q_text.pack(anchor="w", pady=(0, 15))

        # Radio options
        self.selected_option_var = tk.StringVar(value="")
        self.option_radios = {}

        for opt_key in ["A", "B", "C", "D"]:
            r = tk.Radiobutton(
                self.q_card,
                text="",
                variable=self.selected_option_var,
                value=opt_key,
                bg="#FFFFFF",
                activebackground="#FFFFFF",
                font=("Helvetica", 11),
                command=self.on_option_selected
            )
            r.pack(anchor="w", padx=15, pady=6)
            self.option_radios[opt_key] = r

        # Controls bottom bar
        ctrl_frame = ttk.Frame(self.q_card, style="Card.TFrame")
        ctrl_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))

        self.btn_prev = ttk.Button(ctrl_frame, text="⮜ Previous", command=self.prev_question)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(ctrl_frame, text="Clear Answer", command=self.clear_answer)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.btn_next = ttk.Button(ctrl_frame, text="Next ⮞", command=self.next_question)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.btn_submit = ttk.Button(ctrl_frame, text="Submit Quiz ✓", style="Danger.TButton", command=self.confirm_and_submit_quiz)
        self.btn_submit.pack(side=tk.RIGHT, padx=5)

        self.load_question(self.current_q_index)

    def load_question(self, index):
        q = self.current_questions[index]
        total_q = len(self.current_questions)
        self.lbl_q_num.config(text=f"Question {index + 1} of {total_q}  (Marks: {q['marks']})")
        self.lbl_q_text.config(text=q["question_text"])

        # Set radio text
        self.option_radios["A"].config(text=f"A) {q['option_a']}")
        self.option_radios["B"].config(text=f"B) {q['option_b']}")
        self.option_radios["C"].config(text=f"C) {q['option_c']}")
        self.option_radios["D"].config(text=f"D) {q['option_d']}")

        # Restore previously selected option if any
        prev_ans = self.user_answers.get(q["id"], "")
        self.selected_option_var.set(prev_ans)

        # Enable/disable nav buttons
        self.btn_prev.config(state="normal" if index > 0 else "disabled")
        self.btn_next.config(state="normal" if index < total_q - 1 else "disabled")

    def on_option_selected(self):
        q = self.current_questions[self.current_q_index]
        self.user_answers[q["id"]] = self.selected_option_var.get()

    def clear_answer(self):
        q = self.current_questions[self.current_q_index]
        self.selected_option_var.set("")
        if q["id"] in self.user_answers:
            del self.user_answers[q["id"]]

    def prev_question(self):
        if self.current_q_index > 0:
            self.current_q_index -= 1
            self.load_question(self.current_q_index)

    def next_question(self):
        if self.current_q_index < len(self.current_questions) - 1:
            self.current_q_index += 1
            self.load_question(self.current_q_index)

    def start_timer_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_timer_display()
            self.timer_after_id = self.after(1000, self.start_timer_tick)
        else:
            messagebox.showinfo("Time's Up!", "The quiz time limit has expired. Automatically submitting your answers.")
            self.submit_quiz(auto=True)

    def update_timer_display(self):
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.lbl_timer.config(text=f"⏳ Time Remaining: {mins:02d}:{secs:02d}")

    def confirm_and_submit_quiz(self):
        total_q = len(self.current_questions)
        answered = len(self.user_answers)
        unanswered = total_q - answered

        msg = f"You have answered {answered} out of {total_q} questions.\n"
        if unanswered > 0:
            msg += f"Warning: {unanswered} questions are still unanswered!\n\n"
        msg += "Are you sure you want to finalize and submit?"

        if messagebox.askyesno("Confirm Submission", msg):
            self.submit_quiz(auto=False)

    def submit_quiz(self, auto=False):
        if self.timer_after_id:
            self.after_cancel(self.timer_after_id)
            self.timer_after_id = None

        # Automated Grading Engine
        total_marks = 0
        scored_marks = 0
        detailed_results = []

        for q in self.current_questions:
            total_marks += q["marks"]
            user_choice = self.user_answers.get(q["id"], "None")
            is_correct = (user_choice == q["correct_option"])
            if is_correct:
                scored_marks += q["marks"]

            detailed_results.append({
                "question": q["question_text"],
                "user_choice": user_choice,
                "correct_option": q["correct_option"],
                "is_correct": is_correct,
                "marks": q["marks"]
            })

        percentage = round((scored_marks / total_marks * 100) if total_marks > 0 else 0, 2)
        pass_cutoff = float(self.current_quiz["pass_percentage"])
        status = "Passed" if percentage >= pass_cutoff else "Failed"

        # Save into SQLite database
        database.save_attempt(
            student_name=self.student_name,
            student_roll=self.student_roll,
            quiz_id=self.current_quiz["id"],
            score=scored_marks,
            total_marks=total_marks,
            percentage=percentage,
            status=status
        )

        self.show_results_screen_for_attempt(scored_marks, total_marks, percentage, status, detailed_results)

    # -------------------------------------------------------------
    # SCREEN 3: Instant Automated Results & Review
    # -------------------------------------------------------------
    def show_results_screen_for_attempt(self, scored_marks, total_marks, percentage, status, detailed_results):
        self.clear_container()

        title_lbl = ttk.Label(self.container, text="Quiz Evaluation & Scorecard", style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 10))

        card = ttk.Frame(self.container, style="Card.TFrame", padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        # Summary box
        status_color = "#16A34A" if status == "Passed" else "#DC2626"
        summary_text = (
            f"Student: {self.student_name} ({self.student_roll})\n"
            f"Quiz: {self.current_quiz['title']}\n"
            f"Score: {scored_marks} / {total_marks}  ({percentage}%)\n"
            f"Outcome: {status.upper()}"
        )
        lbl_sum = tk.Label(card, text=summary_text, font=("Helvetica", 12, "bold"), fg=status_color, bg="#FFFFFF", justify="left")
        lbl_sum.pack(anchor="w", pady=(0, 15))

        # Question review treeview
        lbl_rev = ttk.Label(card, text="Detailed Question Breakdown:", style="CardLabel.TLabel")
        lbl_rev.pack(anchor="w", pady=(5, 5))

        cols = ("#", "Question", "Your Answer", "Correct Answer", "Result")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=8)
        tree.heading("#", text="#")
        tree.heading("Question", text="Question Text")
        tree.heading("Your Answer", text="Your Choice")
        tree.heading("Correct Answer", text="Correct Key")
        tree.heading("Result", text="Marks / Result")

        tree.column("#", width=40, anchor="center")
        tree.column("Question", width=450)
        tree.column("Your Answer", width=100, anchor="center")
        tree.column("Correct Answer", width=100, anchor="center")
        tree.column("Result", width=120, anchor="center")

        for idx, item in enumerate(detailed_results, 1):
            res_str = f"✓ Correct (+{item['marks']})" if item["is_correct"] else "✗ Incorrect (0)"
            tree.insert("", tk.END, values=(idx, item["question"], item["user_choice"], item["correct_option"], res_str))

        tree.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_home = ttk.Button(card, text="Return to Home Screen", style="Primary.TButton", command=self.show_home_screen)
        btn_home.pack(anchor="w", pady=12)

    # -------------------------------------------------------------
    # SCREEN 4: Admin CRUD Management
    # -------------------------------------------------------------
    def show_admin_screen(self):
        self.clear_container()

        title_lbl = ttk.Label(self.container, text="Quiz & Question Management (CRUD)", style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 10))

        notebook = ttk.Notebook(self.container)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Quiz CRUD
        tab_quizzes = ttk.Frame(notebook, padding=15)
        notebook.add(tab_quizzes, text="  Quizzes Manager  ")
        self.build_quiz_crud_tab(tab_quizzes)

        # Tab 2: Question CRUD
        tab_questions = ttk.Frame(notebook, padding=15)
        notebook.add(tab_questions, text="  Questions Manager  ")
        self.build_question_crud_tab(tab_questions)

    def build_quiz_crud_tab(self, parent):
        # Top list of quizzes
        list_frame = ttk.LabelFrame(parent, text="Existing Quizzes", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        cols = ("ID", "Title", "Time Limit", "Pass %", "Questions Count")
        self.quiz_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=5)
        for c in cols:
            self.quiz_tree.heading(c, text=c)
        self.quiz_tree.column("ID", width=50, anchor="center")
        self.quiz_tree.column("Title", width=350)
        self.quiz_tree.column("Time Limit", width=100, anchor="center")
        self.quiz_tree.column("Pass %", width=100, anchor="center")
        self.quiz_tree.column("Questions Count", width=120, anchor="center")
        self.quiz_tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_quizzes_list()

        # Form to add / edit quiz
        form_frame = ttk.LabelFrame(parent, text="Add / Edit Quiz", padding=10)
        form_frame.pack(fill=tk.X)

        ttk.Label(form_frame, text="Quiz Title:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_q_title = ttk.Entry(form_frame, width=35)
        self.entry_q_title.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Time Limit (mins):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.entry_q_time = ttk.Entry(form_frame, width=10)
        self.entry_q_time.insert(0, "10")
        self.entry_q_time.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.entry_q_desc = ttk.Entry(form_frame, width=35)
        self.entry_q_desc.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Pass Cutoff %:").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.entry_q_pass = ttk.Entry(form_frame, width=10)
        self.entry_q_pass.insert(0, "50.0")
        self.entry_q_pass.grid(row=1, column=3, sticky="w", padx=5, pady=4)

        # Buttons
        btn_bar = ttk.Frame(form_frame)
        btn_bar.grid(row=2, column=0, columnspan=4, pady=8, sticky="w")

        ttk.Button(btn_bar, text="Save New Quiz", style="Success.TButton", command=self.save_new_quiz).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="Delete Selected Quiz", style="Danger.TButton", command=self.delete_selected_quiz).pack(side=tk.LEFT, padx=5)

    def refresh_quizzes_list(self):
        for item in self.quiz_tree.get_children():
            self.quiz_tree.delete(item)
        quizzes = database.get_all_quizzes()
        for q in quizzes:
            self.quiz_tree.insert("", tk.END, values=(q["id"], q["title"], f"{q['time_limit_mins']} mins", f"{q['pass_percentage']}%", q["question_count"]))

    def save_new_quiz(self):
        title = self.entry_q_title.get().strip()
        desc = self.entry_q_desc.get().strip()
        time_limit = self.entry_q_time.get().strip()
        pass_cut = self.entry_q_pass.get().strip()

        if not title:
            messagebox.showwarning("Validation Error", "Quiz title cannot be empty.")
            return

        try:
            t = int(time_limit)
            p = float(pass_cut)
        except ValueError:
            messagebox.showwarning("Validation Error", "Time limit and pass % must be numeric numbers.")
            return

        try:
            database.create_quiz(title, desc, t, p)
            messagebox.showinfo("Success", f"Quiz '{title}' created successfully!")
            self.entry_q_title.delete(0, tk.END)
            self.entry_q_desc.delete(0, tk.END)
            self.refresh_quizzes_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save quiz: {e}")

    def delete_selected_quiz(self):
        selected = self.quiz_tree.selection()
        if not selected:
            messagebox.showwarning("Select Quiz", "Please select a quiz from the table to delete.")
            return

        values = self.quiz_tree.item(selected[0], "values")
        quiz_id = values[0]
        quiz_title = values[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete quiz '{quiz_title}' and all its questions?"):
            database.delete_quiz(quiz_id)
            messagebox.showinfo("Deleted", "Quiz deleted successfully.")
            self.refresh_quizzes_list()

    def build_question_crud_tab(self, parent):
        # Selector for Quiz
        top_filter = ttk.Frame(parent)
        top_filter.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(top_filter, text="Select Quiz to Manage Questions:").pack(side=tk.LEFT, padx=5)
        self.manage_quizzes_data = database.get_all_quizzes()
        opts = [f"{q['id']} - {q['title']}" for q in self.manage_quizzes_data]
        self.combo_filter_quiz = ttk.Combobox(top_filter, values=opts, width=40, state="readonly")
        if opts:
            self.combo_filter_quiz.current(0)
        self.combo_filter_quiz.pack(side=tk.LEFT, padx=5)

        self.combo_filter_quiz.bind("<<ComboboxSelected>>", lambda e: self.refresh_questions_list())

        # Questions list
        cols = ("ID", "Question", "Opt A", "Opt B", "Opt C", "Opt D", "Answer", "Marks")
        self.question_tree = ttk.Treeview(parent, columns=cols, show="headings", height=5)
        for c in cols:
            self.question_tree.heading(c, text=c)
        self.question_tree.column("ID", width=40, anchor="center")
        self.question_tree.column("Question", width=300)
        self.question_tree.column("Opt A", width=80)
        self.question_tree.column("Opt B", width=80)
        self.question_tree.column("Opt C", width=80)
        self.question_tree.column("Opt D", width=80)
        self.question_tree.column("Answer", width=60, anchor="center")
        self.question_tree.column("Marks", width=50, anchor="center")
        self.question_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Form for Add Question
        f = ttk.LabelFrame(parent, text="Add New Question to Selected Quiz", padding=10)
        f.pack(fill=tk.X, pady=(8, 0))

        ttk.Label(f, text="Question:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.e_q_text = ttk.Entry(f, width=45)
        self.e_q_text.grid(row=0, column=1, columnspan=3, sticky="we", padx=4, pady=3)

        ttk.Label(f, text="Option A:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.e_opt_a = ttk.Entry(f, width=22)
        self.e_opt_a.grid(row=1, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(f, text="Option B:").grid(row=1, column=2, sticky="w", padx=4, pady=3)
        self.e_opt_b = ttk.Entry(f, width=22)
        self.e_opt_b.grid(row=1, column=3, sticky="w", padx=4, pady=3)

        ttk.Label(f, text="Option C:").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.e_opt_c = ttk.Entry(f, width=22)
        self.e_opt_c.grid(row=2, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(f, text="Option D:").grid(row=2, column=2, sticky="w", padx=4, pady=3)
        self.e_opt_d = ttk.Entry(f, width=22)
        self.e_opt_d.grid(row=2, column=3, sticky="w", padx=4, pady=3)

        ttk.Label(f, text="Correct Answer:").grid(row=3, column=0, sticky="w", padx=4, pady=3)
        self.combo_ans = ttk.Combobox(f, values=["A", "B", "C", "D"], width=10, state="readonly")
        self.combo_ans.current(0)
        self.combo_ans.grid(row=3, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(f, text="Marks:").grid(row=3, column=2, sticky="w", padx=4, pady=3)
        self.e_marks = ttk.Entry(f, width=10)
        self.e_marks.insert(0, "1")
        self.e_marks.grid(row=3, column=3, sticky="w", padx=4, pady=3)

        btn_box = ttk.Frame(f)
        btn_box.grid(row=4, column=0, columnspan=4, pady=6, sticky="w")

        ttk.Button(btn_box, text="Add Question", style="Success.TButton", command=self.save_new_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Delete Selected Question", style="Danger.TButton", command=self.delete_selected_question).pack(side=tk.LEFT, padx=5)

        self.refresh_questions_list()

    def get_current_selected_quiz_id(self):
        idx = self.combo_filter_quiz.current()
        if idx >= 0 and idx < len(self.manage_quizzes_data):
            return self.manage_quizzes_data[idx]["id"]
        return None

    def refresh_questions_list(self):
        for item in self.question_tree.get_children():
            self.question_tree.delete(item)
        quiz_id = self.get_current_selected_quiz_id()
        if not quiz_id:
            return
        questions = database.get_questions_by_quiz(quiz_id)
        for q in questions:
            self.question_tree.insert("", tk.END, values=(
                q["id"], q["question_text"], q["option_a"], q["option_b"], q["option_c"], q["option_d"], q["correct_option"], q["marks"]
            ))

    def save_new_question(self):
        quiz_id = self.get_current_selected_quiz_id()
        if not quiz_id:
            messagebox.showwarning("Select Quiz", "Please select a quiz first.")
            return

        text = self.e_q_text.get().strip()
        opt_a = self.e_opt_a.get().strip()
        opt_b = self.e_opt_b.get().strip()
        opt_c = self.e_opt_c.get().strip()
        opt_d = self.e_opt_d.get().strip()
        ans = self.combo_ans.get()
        marks = self.e_marks.get().strip()

        if not text or not opt_a or not opt_b or not opt_c or not opt_d:
            messagebox.showwarning("Validation Error", "Please provide question text and all 4 options.")
            return

        try:
            m = int(marks)
        except ValueError:
            m = 1

        database.add_question(quiz_id, text, opt_a, opt_b, opt_c, opt_d, ans, m)
        messagebox.showinfo("Success", "Question added successfully!")

        self.e_q_text.delete(0, tk.END)
        self.e_opt_a.delete(0, tk.END)
        self.e_opt_b.delete(0, tk.END)
        self.e_opt_c.delete(0, tk.END)
        self.e_opt_d.delete(0, tk.END)
        self.refresh_questions_list()

    def delete_selected_question(self):
        selected = self.question_tree.selection()
        if not selected:
            messagebox.showwarning("Select Question", "Please select a question to delete.")
            return
        q_id = self.question_tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this question?"):
            database.delete_question(q_id)
            messagebox.showinfo("Deleted", "Question deleted.")
            self.refresh_questions_list()

    # -------------------------------------------------------------
    # SCREEN 5: Student Results & Gradebook
    # -------------------------------------------------------------
    def show_results_screen(self):
        self.clear_container()

        title_lbl = ttk.Label(self.container, text="Student Quiz Results & Performance History", style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 10))

        card = ttk.Frame(self.container, style="Card.TFrame", padding=15)
        card.pack(fill=tk.BOTH, expand=True)

        attempts = database.get_all_attempts()

        # Stats bar
        total_attempts = len(attempts)
        pass_count = sum(1 for a in attempts if a["status"] == "Passed")
        pass_rate = round((pass_count / total_attempts * 100) if total_attempts > 0 else 0, 1)

        stats_frame = ttk.Frame(card, style="Card.TFrame")
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(stats_frame, text=f"Total Attempts: {total_attempts}  |  Passed: {pass_count}  |  Pass Rate: {pass_rate}%",
                  font=("Helvetica", 11, "bold"), background="#FFFFFF", foreground="#1E40AF").pack(side=tk.LEFT)

        cols = ("ID", "Student Name", "Roll No", "Quiz Title", "Score", "Total", "Percentage", "Status", "Date")
        tree = ttk.Treeview(card, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=40, anchor="center")
        tree.column("Student Name", width=160)
        tree.column("Roll No", width=120, anchor="center")
        tree.column("Quiz Title", width=200)
        tree.column("Score", width=60, anchor="center")
        tree.column("Total", width=60, anchor="center")
        tree.column("Percentage", width=90, anchor="center")
        tree.column("Status", width=90, anchor="center")
        tree.column("Date", width=150, anchor="center")

        for a in attempts:
            tree.insert("", tk.END, values=(
                a["id"], a["student_name"], a["student_roll"], a["quiz_title"], a["score"], a["total_marks"], f"{a['percentage']}%", a["status"], a["completed_at"]
            ))

        tree.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------
    # SCREEN 6: TQM Quality Audit & Defect Log
    # -------------------------------------------------------------
    def show_tqm_logs_screen(self):
        self.clear_container()

        title_lbl = ttk.Label(self.container, text="TQM Quality Audit, Checksheets & Defect Logs", style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 5))

        desc_lbl = ttk.Label(self.container, text="Live Statistical Quality Control (SQC) audit trail and continuous improvement tracker.", style="SubTitle.TLabel")
        desc_lbl.pack(anchor="w", pady=(0, 10))

        card = ttk.Frame(self.container, style="Card.TFrame", padding=15)
        card.pack(fill=tk.BOTH, expand=True)

        # Principles Banner
        banner = ttk.Label(card, text="Applied TQM Methodologies: Customer Focus, Kaizen (Continuous Improvement), SIPOC Mapping, Poka-Yoke (Error Prevention)",
                           font=("Helvetica", 10, "italic"), background="#FFFFFF", foreground="#4338CA")
        banner.pack(anchor="w", pady=(0, 10))

        # Defect Table
        cols = ("ID", "Defect / Audit Category", "Description", "Severity", "Status", "Logged At")
        tree = ttk.Treeview(card, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=40, anchor="center")
        tree.column("Defect / Audit Category", width=180)
        tree.column("Description", width=340)
        tree.column("Severity", width=90, anchor="center")
        tree.column("Status", width=90, anchor="center")
        tree.column("Logged At", width=150, anchor="center")

        defects = database.get_all_defects()
        for d in defects:
            tree.insert("", tk.END, values=(d["id"], d["category"], d["description"], d["severity"], d["status"], d["logged_at"]))

        tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Quick Log Defect Entry
        f = ttk.LabelFrame(card, text="Record Defect / Quality Check (PDCA)", padding=10)
        f.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(f, text="Category:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        combo_cat = ttk.Combobox(f, values=["Input Validation", "Response Latency", "Database Consistency", "UI Usability", "Grading Logic"], state="readonly")
        combo_cat.current(0)
        combo_cat.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(f, text="Severity:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        combo_sev = ttk.Combobox(f, values=["Low", "Medium", "High", "Critical"], state="readonly", width=10)
        combo_sev.current(1)
        combo_sev.grid(row=0, column=3, sticky="w", padx=5, pady=2)

        ttk.Label(f, text="Description:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        entry_desc = ttk.Entry(f, width=50)
        entry_desc.grid(row=1, column=1, columnspan=3, sticky="we", padx=5, pady=4)

        def add_defect_entry():
            c = combo_cat.get()
            s = combo_sev.get()
            d = entry_desc.get().strip()
            if not d:
                messagebox.showwarning("Required", "Please provide a description of the defect or audit event.")
                return
            database.log_defect(c, d, s, "Open")
            messagebox.showinfo("Logged", "Defect recorded to TQM Checksheet successfully.")
            self.show_tqm_logs_screen()

        btn_add_def = ttk.Button(f, text="Log Defect to Checksheet", style="Primary.TButton", command=add_defect_entry)
        btn_add_def.grid(row=2, column=0, columnspan=4, pady=5, sticky="w")


def run_app():
    database.init_db()
    app = QuizApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()
