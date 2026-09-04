import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from db import Database
from utils import calculate_percentage, calculate_grade, export_rows_to_csv

APP_TITLE = "Student Success Hub - Academic Planner & Performance Analyzer"

class StudentSuccessHub(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1150x700")
        self.minsize(1000, 620)

        self.db = Database("student_success.db")
        self.db.initialize()

        self.configure(bg="#f4f7fb")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self._configure_styles()

        self.current_student_id = None
        self._build_ui()
        self.refresh_students()
        self.refresh_tasks()
        self.refresh_dashboard()

    def _configure_styles(self):
        self.style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#f4f7fb")
        self.style.configure("SubTitle.TLabel", font=("Segoe UI", 11), background="#f4f7fb", foreground="#555")
        self.style.configure("Card.TFrame", background="white", relief="flat")
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"), background="white")
        self.style.configure("CardValue.TLabel", font=("Segoe UI", 23, "bold"), background="white")
        self.style.configure("TButton", padding=7)
        self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        header = ttk.Frame(self, padding=(20, 16))
        header.pack(fill="x")
        ttk.Label(header, text="Student Success Hub", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Academic planner, marks tracker, attendance manager and performance analyzer",
            style="SubTitle.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.dashboard_tab = ttk.Frame(self.notebook, padding=15)
        self.students_tab = ttk.Frame(self.notebook, padding=15)
        self.marks_tab = ttk.Frame(self.notebook, padding=15)
        self.attendance_tab = ttk.Frame(self.notebook, padding=15)
        self.tasks_tab = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.students_tab, text="Students")
        self.notebook.add(self.marks_tab, text="Marks")
        self.notebook.add(self.attendance_tab, text="Attendance")
        self.notebook.add(self.tasks_tab, text="Study Tasks")

        self._build_dashboard()
        self._build_students()
        self._build_marks()
        self._build_attendance()
        self._build_tasks()

    # ---------------- Dashboard ----------------
    def _build_dashboard(self):
        top = ttk.Frame(self.dashboard_tab)
        top.pack(fill="x")

        self.card_vars = {
            "students": tk.StringVar(value="0"),
            "tasks": tk.StringVar(value="0"),
            "avg": tk.StringVar(value="0%"),
            "attendance": tk.StringVar(value="0%"),
        }

        cards = [
            ("Total Students", "students"),
            ("Pending Tasks", "tasks"),
            ("Average Marks", "avg"),
            ("Average Attendance", "attendance"),
        ]
        for i, (title, key) in enumerate(cards):
            frame = ttk.Frame(top, style="Card.TFrame", padding=18)
            frame.grid(row=0, column=i, padx=7, sticky="nsew")
            top.columnconfigure(i, weight=1)
            ttk.Label(frame, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(frame, textvariable=self.card_vars[key], style="CardValue.TLabel").pack(anchor="w", pady=(10, 0))

        lower = ttk.Frame(self.dashboard_tab)
        lower.pack(fill="both", expand=True, pady=(18, 0))
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(lower, text="Student Performance Summary", padding=10)
        right = ttk.LabelFrame(lower, text="Upcoming / Pending Tasks", padding=10)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        self.dashboard_student_tree = ttk.Treeview(left, columns=("name","dept","avg","grade"), show="headings")
        for col, text, width in [("name","Name",160),("dept","Department",120),("avg","Average %",90),("grade","Grade",70)]:
            self.dashboard_student_tree.heading(col, text=text)
            self.dashboard_student_tree.column(col, width=width, anchor="center")
        self.dashboard_student_tree.pack(fill="both", expand=True)

        self.dashboard_task_tree = ttk.Treeview(right, columns=("title","student","due","priority"), show="headings")
        for col, text, width in [("title","Task",180),("student","Student",120),("due","Due Date",100),("priority","Priority",80)]:
            self.dashboard_task_tree.heading(col, text=text)
            self.dashboard_task_tree.column(col, width=width, anchor="center")
        self.dashboard_task_tree.pack(fill="both", expand=True)

    def refresh_dashboard(self):
        students = self.db.get_students()
        tasks = self.db.get_tasks(status="Pending")
        marks = self.db.get_all_marks()
        attendance = self.db.get_all_attendance()

        self.card_vars["students"].set(str(len(students)))
        self.card_vars["tasks"].set(str(len(tasks)))

        if marks:
            percentages = [calculate_percentage(r[3], r[4]) for r in marks]
            self.card_vars["avg"].set(f"{sum(percentages)/len(percentages):.1f}%")
        else:
            self.card_vars["avg"].set("0%")

        if attendance:
            vals = [(r[3] / r[2] * 100) if r[2] else 0 for r in attendance]
            self.card_vars["attendance"].set(f"{sum(vals)/len(vals):.1f}%")
        else:
            self.card_vars["attendance"].set("0%")

        for item in self.dashboard_student_tree.get_children():
            self.dashboard_student_tree.delete(item)
        for student in students:
            sid, name, roll, dept, sem = student
            smarks = self.db.get_marks_by_student(sid)
            if smarks:
                ps = [calculate_percentage(r[3], r[4]) for r in smarks]
                avg = sum(ps)/len(ps)
            else:
                avg = 0
            self.dashboard_student_tree.insert("", "end", values=(name, dept, f"{avg:.1f}", calculate_grade(avg)))

        for item in self.dashboard_task_tree.get_children():
            self.dashboard_task_tree.delete(item)
        for row in tasks[:20]:
            self.dashboard_task_tree.insert("", "end", values=(row[2], row[7], row[4], row[5]))

    # ---------------- Students ----------------
    def _build_students(self):
        form = ttk.LabelFrame(self.students_tab, text="Student Details", padding=12)
        form.pack(fill="x")

        labels = ["Name", "Roll Number", "Department", "Semester"]
        self.student_vars = [tk.StringVar() for _ in labels]
        for i, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=5, pady=4, sticky="w")
            ttk.Entry(form, textvariable=self.student_vars[i], width=23).grid(row=1, column=i, padx=5, pady=4)

        ttk.Button(form, text="Add Student", command=self.add_student).grid(row=1, column=4, padx=8)
        ttk.Button(form, text="Delete Selected", command=self.delete_student).grid(row=1, column=5, padx=8)

        self.student_tree = ttk.Treeview(
            self.students_tab,
            columns=("id","name","roll","dept","sem"),
            show="headings"
        )
        heads = [("id","ID",50),("name","Name",220),("roll","Roll No.",130),("dept","Department",180),("sem","Semester",90)]
        for col, txt, width in heads:
            self.student_tree.heading(col, text=txt)
            self.student_tree.column(col, width=width, anchor="center")
        self.student_tree.pack(fill="both", expand=True, pady=(12, 0))

    def add_student(self):
        values = [v.get().strip() for v in self.student_vars]
        if not all(values):
            messagebox.showwarning("Missing Data", "Please fill all student fields.")
            return
        try:
            self.db.add_student(values[0], values[1], values[2], values[3])
            for v in self.student_vars:
                v.set("")
            self.refresh_students()
            self.refresh_dashboard()
            messagebox.showinfo("Success", "Student added successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_student(self):
        selected = self.student_tree.selection()
        if not selected:
            messagebox.showwarning("Select Student", "Please select a student.")
            return
        item = self.student_tree.item(selected[0])
        sid = item["values"][0]
        if messagebox.askyesno("Confirm", "Delete selected student and related academic records?"):
            self.db.delete_student(sid)
            self.refresh_students()
            self.refresh_tasks()
            self.refresh_dashboard()

    def refresh_students(self):
        rows = self.db.get_students()
        for item in getattr(self, "student_tree", ttk.Treeview()).get_children():
            self.student_tree.delete(item)
        if hasattr(self, "student_tree"):
            for row in rows:
                self.student_tree.insert("", "end", values=row)

        student_names = [f"{r[0]} - {r[1]} ({r[2]})" for r in rows]
        if hasattr(self, "marks_student_combo"):
            self.marks_student_combo["values"] = student_names
        if hasattr(self, "attendance_student_combo"):
            self.attendance_student_combo["values"] = student_names
        if hasattr(self, "task_student_combo"):
            self.task_student_combo["values"] = student_names

    def _selected_student_id(self, combo_value):
        try:
            return int(combo_value.split(" - ")[0].strip())
        except Exception:
            return None

    # ---------------- Marks ----------------
    def _build_marks(self):
        form = ttk.LabelFrame(self.marks_tab, text="Enter Subject Marks", padding=12)
        form.pack(fill="x")

        self.marks_student = tk.StringVar()
        self.marks_subject = tk.StringVar()
        self.marks_score = tk.StringVar()
        self.marks_max = tk.StringVar(value="100")

        fields = [
            ("Student", self.marks_student),
            ("Subject", self.marks_subject),
            ("Marks Obtained", self.marks_score),
            ("Maximum Marks", self.marks_max),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=5, sticky="w")
            if i == 0:
                self.marks_student_combo = ttk.Combobox(form, textvariable=var, state="readonly", width=28)
                self.marks_student_combo.grid(row=1, column=i, padx=5, pady=5)
            else:
                ttk.Entry(form, textvariable=var, width=22).grid(row=1, column=i, padx=5, pady=5)

        ttk.Button(form, text="Save Marks", command=self.add_marks).grid(row=1, column=4, padx=8)
        ttk.Button(form, text="Export CSV", command=self.export_marks).grid(row=1, column=5, padx=8)

        self.marks_tree = ttk.Treeview(
            self.marks_tab,
            columns=("id","student","subject","score","max","percent","grade"),
            show="headings"
        )
        cols = [
            ("id","ID",45),("student","Student",180),("subject","Subject",160),
            ("score","Marks",75),("max","Max",70),("percent","%",70),("grade","Grade",70)
        ]
        for c,t,w in cols:
            self.marks_tree.heading(c, text=t)
            self.marks_tree.column(c, width=w, anchor="center")
        self.marks_tree.pack(fill="both", expand=True, pady=(12,0))
        self.refresh_marks()

    def add_marks(self):
        sid = self._selected_student_id(self.marks_student.get())
        subject = self.marks_subject.get().strip()
        try:
            score = float(self.marks_score.get())
            maximum = float(self.marks_max.get())
        except ValueError:
            messagebox.showwarning("Invalid Marks", "Marks must be numeric.")
            return
        if not sid or not subject or maximum <= 0 or score < 0 or score > maximum:
            messagebox.showwarning("Invalid Data", "Check student, subject and marks values.")
            return
        self.db.add_marks(sid, subject, score, maximum)
        self.marks_subject.set("")
        self.marks_score.set("")
        self.refresh_marks()
        self.refresh_dashboard()

    def refresh_marks(self):
        if not hasattr(self, "marks_tree"):
            return
        for item in self.marks_tree.get_children():
            self.marks_tree.delete(item)
        for row in self.db.get_marks_with_students():
            percent = calculate_percentage(row[3], row[4])
            self.marks_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], f"{percent:.1f}", calculate_grade(percent)))

    def export_marks(self):
        rows = []
        for row in self.db.get_marks_with_students():
            percent = calculate_percentage(row[3], row[4])
            rows.append([row[1], row[2], row[3], row[4], round(percent,2), calculate_grade(percent)])
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
        if path:
            export_rows_to_csv(path, ["Student","Subject","Marks","Maximum","Percentage","Grade"], rows)
            messagebox.showinfo("Exported", "Marks report exported successfully.")

    # ---------------- Attendance ----------------
    def _build_attendance(self):
        form = ttk.LabelFrame(self.attendance_tab, text="Attendance Entry", padding=12)
        form.pack(fill="x")

        self.att_student = tk.StringVar()
        self.att_subject = tk.StringVar()
        self.att_total = tk.StringVar()
        self.att_present = tk.StringVar()

        entries = [
            ("Student", self.att_student),
            ("Subject", self.att_subject),
            ("Total Classes", self.att_total),
            ("Classes Present", self.att_present),
        ]
        for i, (label, var) in enumerate(entries):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=5, sticky="w")
            if i == 0:
                self.attendance_student_combo = ttk.Combobox(form, textvariable=var, state="readonly", width=28)
                self.attendance_student_combo.grid(row=1, column=i, padx=5, pady=5)
            else:
                ttk.Entry(form, textvariable=var, width=22).grid(row=1, column=i, padx=5, pady=5)

        ttk.Button(form, text="Save Attendance", command=self.add_attendance).grid(row=1, column=4, padx=8)

        self.att_tree = ttk.Treeview(
            self.attendance_tab,
            columns=("id","student","subject","total","present","percentage","status"),
            show="headings"
        )
        cols = [
            ("id","ID",45),("student","Student",180),("subject","Subject",160),
            ("total","Total",70),("present","Present",70),("percentage","%",70),("status","Status",110)
        ]
        for c,t,w in cols:
            self.att_tree.heading(c, text=t)
            self.att_tree.column(c, width=w, anchor="center")
        self.att_tree.pack(fill="both", expand=True, pady=(12,0))
        self.refresh_attendance()

    def add_attendance(self):
        sid = self._selected_student_id(self.att_student.get())
        subject = self.att_subject.get().strip()
        try:
            total = int(self.att_total.get())
            present = int(self.att_present.get())
        except ValueError:
            messagebox.showwarning("Invalid Data", "Attendance values must be integers.")
            return
        if not sid or not subject or total <= 0 or present < 0 or present > total:
            messagebox.showwarning("Invalid Data", "Check attendance values.")
            return
        self.db.add_attendance(sid, subject, total, present)
        self.att_subject.set("")
        self.att_total.set("")
        self.att_present.set("")
        self.refresh_attendance()
        self.refresh_dashboard()

    def refresh_attendance(self):
        if not hasattr(self, "att_tree"):
            return
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        for row in self.db.get_attendance_with_students():
            pct = (row[4]/row[3]*100) if row[3] else 0
            status = "Good" if pct >= 75 else "Shortage"
            self.att_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], f"{pct:.1f}", status))

    # ---------------- Tasks ----------------
    def _build_tasks(self):
        form = ttk.LabelFrame(self.tasks_tab, text="Study Task Planner", padding=12)
        form.pack(fill="x")

        self.task_student = tk.StringVar()
        self.task_title = tk.StringVar()
        self.task_due = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.task_priority = tk.StringVar(value="Medium")

        ttk.Label(form, text="Student").grid(row=0,column=0,padx=5,sticky="w")
        self.task_student_combo = ttk.Combobox(form, textvariable=self.task_student, state="readonly", width=28)
        self.task_student_combo.grid(row=1,column=0,padx=5,pady=5)

        ttk.Label(form, text="Task").grid(row=0,column=1,padx=5,sticky="w")
        ttk.Entry(form, textvariable=self.task_title, width=30).grid(row=1,column=1,padx=5,pady=5)

        ttk.Label(form, text="Due Date (YYYY-MM-DD)").grid(row=0,column=2,padx=5,sticky="w")
        ttk.Entry(form, textvariable=self.task_due, width=20).grid(row=1,column=2,padx=5,pady=5)

        ttk.Label(form, text="Priority").grid(row=0,column=3,padx=5,sticky="w")
        ttk.Combobox(form, textvariable=self.task_priority, values=["Low","Medium","High"], state="readonly", width=15).grid(row=1,column=3,padx=5,pady=5)

        ttk.Button(form, text="Add Task", command=self.add_task).grid(row=1,column=4,padx=8)
        ttk.Button(form, text="Mark Completed", command=self.complete_task).grid(row=1,column=5,padx=8)

        self.task_tree = ttk.Treeview(
            self.tasks_tab,
            columns=("id","student","task","due","priority","status"),
            show="headings"
        )
        cols = [
            ("id","ID",45),("student","Student",170),("task","Task",260),
            ("due","Due Date",110),("priority","Priority",90),("status","Status",100)
        ]
        for c,t,w in cols:
            self.task_tree.heading(c, text=t)
            self.task_tree.column(c, width=w, anchor="center")
        self.task_tree.pack(fill="both", expand=True, pady=(12,0))

    def add_task(self):
        sid = self._selected_student_id(self.task_student.get())
        title = self.task_title.get().strip()
        due = self.task_due.get().strip()
        priority = self.task_priority.get().strip()

        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid Date", "Use YYYY-MM-DD format.")
            return

        if not sid or not title:
            messagebox.showwarning("Missing Data", "Select a student and enter a task.")
            return

        self.db.add_task(sid, title, due, priority)
        self.task_title.set("")
        self.refresh_tasks()
        self.refresh_dashboard()

    def complete_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Select Task", "Please select a task.")
            return
        task_id = self.task_tree.item(selected[0])["values"][0]
        self.db.update_task_status(task_id, "Completed")
        self.refresh_tasks()
        self.refresh_dashboard()

    def refresh_tasks(self):
        if not hasattr(self, "task_tree"):
            return
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        for row in self.db.get_tasks():
            self.task_tree.insert("", "end", values=(row[0], row[7], row[2], row[4], row[5], row[6]))

if __name__ == "__main__":
    app = StudentSuccessHub()
    app.mainloop()
