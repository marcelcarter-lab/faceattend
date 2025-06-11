import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import datetime
import time
from pathlib import Path
from PIL import Image, ImageTk
import json
import threading

from password_manager import PasswordManager
from face_trainer import FaceTrainer
from attendance_recorder import AttendanceRecorder
from schedule_manager import ScheduleManager

class FaceAttendanceApp(tk.Tk):
    """
    Application Tkinter pour FaceAttend, single-user.
    - Login/SignUp avec PasswordManager (bcrypt + recovery phrase).
    - Emploi du temps hebdomadaire via ScheduleManager.
    - Capture faces, train model, prise d'appel conditionnée par le planning et auto-déclenchée.
    """

    def __init__(self):
        super().__init__()
        self.title("FaceAttend")
        self.geometry("1000x600")
        self.configure(bg="#f0f0f0")

        # Chemin vers le logo (icône)
        self.logo_path = Path(__file__).parent / "attandance_logo.png"

        # Charger icône de la fenêtre
        if self.logo_path.exists():
            try:
                icon_img = tk.PhotoImage(file=str(self.logo_path))
                self.iconphoto(False, icon_img)
            except tk.TclError:
                pass

        # Instancier les gestionnaires
        self.pwd_mgr = PasswordManager("TrainingImageLabel/credentials.json")
        self.trainer = FaceTrainer(
            haar_path="haarcascade_frontalface_default.xml",
            training_dir="TrainingImage",
            details_csv="StudentDetails/StudentDetails.csv"
        )
        self.recorder = AttendanceRecorder(
            haar_path="haarcascade_frontalface_default.xml",
            model_path="TrainingImageLabel/Trainer.yml",
            details_csv="StudentDetails/StudentDetails.csv"
        )
        self.schedule_mgr = ScheduleManager()
        self.schedule_path = None  # chemin du CSV de planning chargé

        # Chargement config (p. ex. schedule path)
        self.config_path = Path("config.json")
        self._load_config()

        # Construire (mais masquer) l'interface principale
        self._build_main_interface()
        self.withdraw()

        # Créer et afficher la fenêtre de login/sign-up
        self._create_login_window()

    def _load_config(self):
        """
        Charge config JSON (en particulier schedule CSV path) si existant.
        """
        if self.config_path.exists():
            try:
                d = json.load(open(self.config_path))
                sched_path = d.get("schedule_csv")
                if sched_path and Path(sched_path).exists():
                    self.schedule_mgr.load_from_csv(sched_path)
                    self.schedule_path = sched_path
            except Exception:
                pass

    def _save_config(self):
        """
        Sauvegarde le chemin du schedule CSV si défini.
        """
        d = {}
        if self.schedule_path:
            d['schedule_csv'] = self.schedule_path
        with open(self.config_path, "w") as f:
            json.dump(d, f, indent=2)

    def _create_login_window(self):
        """
        Fenêtre Toplevel pour login / sign up.
        """
        self.login_win = tk.Toplevel(self)
        self.login_win.title("FaceAttend – Login")
        self.login_win.geometry("750x400")
        self.login_win.resizable(False, False)
        self.login_win.configure(bg="#ffffff")
        self.login_win.protocol("WM_DELETE_WINDOW", self.destroy)

        w, h = 750, 400
        x = (self.login_win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.login_win.winfo_screenheight() // 2) - (h // 2)
        self.login_win.geometry(f"{w}x{h}+{x}+{y}")

        left_frame = tk.Frame(self.login_win, bg="#4A90E2", width=300, height=400)
        left_frame.pack(side="left", fill="y")

        if self.logo_path.exists():
            try:
                raw_logo = Image.open(self.logo_path)
                small_logo = raw_logo.resize((60, 60), Image.ANTIALIAS)
                self.login_logo_img = ImageTk.PhotoImage(small_logo)
                logo_lbl = tk.Label(left_frame, image=self.login_logo_img, bg="#4A90E2")
                logo_lbl.place(x=10, y=10)
            except Exception:
                pass

        lbl_title = tk.Label(
            left_frame,
            text="Welcome to\nFaceAttend",
            font=("Helvetica", 16, "bold"),
            fg="#ffffff",
            bg="#4A90E2",
            wraplength=240,
            justify="center"
        )
        lbl_title.place(x=20, y=100)

        lbl_sub = tk.Label(
            left_frame,
            text="Please login or sign up\nto continue.",
            font=("Helvetica", 11),
            fg="#e0e0e0",
            bg="#4A90E2",
            wraplength=260,
            justify="center"
        )
        lbl_sub.place(x=20, y=170)

        right_frame = tk.Frame(self.login_win, bg="#ffffff", width=450, height=400)
        right_frame.pack(side="right", fill="both", expand=True)

        form_font = ("Helvetica", 11)
        entry_font = ("Helvetica", 11)
        btn_font = ("Helvetica", 11, "bold")

        if not self.pwd_mgr.is_user_set():
            # Sign Up form
            tk.Label(
                right_frame,
                text="Sign Up",
                font=("Helvetica", 18, "bold"),
                fg="#333333",
                bg="#ffffff"
            ).place(x=30, y=30)

            tk.Label(right_frame, text="Username", font=form_font, bg="#ffffff").place(x=30, y=80)
            self.new_user_ent = tk.Entry(right_frame, font=entry_font)
            self.new_user_ent.place(x=30, y=105, width=280, height=25)

            tk.Label(right_frame, text="Password", font=form_font, bg="#ffffff").place(x=30, y=145)
            self.new_pass_ent = tk.Entry(right_frame, show="*", font=entry_font)
            self.new_pass_ent.place(x=30, y=170, width=280, height=25)

            tk.Label(right_frame, text="Confirm Password", font=form_font, bg="#ffffff").place(x=30, y=210)
            self.confirm_pass_ent = tk.Entry(right_frame, show="*", font=entry_font)
            self.confirm_pass_ent.place(x=30, y=235, width=280, height=25)

            tk.Button(
                right_frame,
                text="Create Account",
                font=btn_font,
                bg="#4A90E2",
                fg="#ffffff",
                activebackground="#357ABD",
                command=self._on_create_user
            ).place(x=30, y=285, width=280, height=30)
        else:
            # Login form
            data = self.pwd_mgr._load()
            remembered = data.get("remember_me", False)
            saved_username = data.get("username", "") if remembered else ""

            tk.Label(
                right_frame,
                text="Login",
                font=("Helvetica", 18, "bold"),
                fg="#333333",
                bg="#ffffff"
            ).place(x=30, y=30)

            tk.Label(right_frame, text="Username", font=form_font, bg="#ffffff").place(x=30, y=80)
            self.login_user_ent = tk.Entry(right_frame, font=entry_font)
            self.login_user_ent.place(x=30, y=105, width=280, height=25)
            if saved_username:
                self.login_user_ent.insert(0, saved_username)

            tk.Label(right_frame, text="Password", font=form_font, bg="#ffffff").place(x=30, y=145)
            self.login_pass_ent = tk.Entry(right_frame, show="*", font=entry_font)
            self.login_pass_ent.place(x=30, y=170, width=280, height=25)

            # Remember me checkbox
            self.remember_var = tk.BooleanVar(value=remembered)
            cb = tk.Checkbutton(
                right_frame,
                text="Remember me",
                variable=self.remember_var,
                bg="#ffffff",
                font=("Helvetica", 10)
            )
            cb.place(x=30, y=205)

            tk.Button(
                right_frame,
                text="Login",
                font=btn_font,
                bg="#4A90E2",
                fg="#ffffff",
                activebackground="#357ABD",
                command=self._on_verify_login
            ).place(x=30, y=240, width=280, height=30)

            # Forgot password link
            forgot_lbl = tk.Label(
                right_frame,
                text="Forgot your password?",
                font=("Helvetica", 10, "underline"),
                fg="#4A90E2",
                bg="#ffffff",
                cursor="hand2"
            )
            forgot_lbl.place(x=30, y=285)
            forgot_lbl.bind("<Button-1>", lambda e: self._on_forgot_from_login())

    def _on_create_user(self):
        username = self.new_user_ent.get().strip()
        pw = self.new_pass_ent.get().strip()
        conf = self.confirm_pass_ent.get().strip()

        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        if not pw:
            messagebox.showerror("Error", "Password cannot be empty.")
            return
        if pw != conf:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        self.pwd_mgr.set_initial_user(username, pw)
        self.login_win.destroy()
        self.deiconify()
        # Lancer auto-attendance si dans session
        self._schedule_auto_attendance()

    def _on_verify_login(self):
        username = self.login_user_ent.get().strip()
        pw = self.login_pass_ent.get().strip()

        if self.pwd_mgr.verify_login(username, pw):
            data = self.pwd_mgr._load()
            data["remember_me"] = self.remember_var.get()
            if data["remember_me"]:
                data["username"] = username
            else:
                data["username"] = ""
            self.pwd_mgr._save(data)

            self.login_win.destroy()
            self.deiconify()
            # Lancer auto-attendance si dans session
            self._schedule_auto_attendance()
        else:
            retry = messagebox.askyesno(
                "Incorrect Credentials",
                "Username or password incorrect.\nDo you want to recover your password?"
            )
            if retry:
                self._on_forgot_from_login()
            else:
                self.login_pass_ent.delete(0, tk.END)

    def _on_forgot_from_login(self):
        success = self.pwd_mgr.recover_password(self.login_win)
        if success:
            self.login_win.destroy()
            self.deiconify()
            self._schedule_auto_attendance()

    def _build_main_interface(self):
        header_frame = tk.Frame(self, bg="#f0f0f0")
        header_frame.pack(fill="x", pady=(5, 0))
        app_name_lbl = tk.Label(
            header_frame,
            text="FaceAttend",
            font=("Helvetica", 20, "bold"),
            fg="#4A90E2",
            bg="#f0f0f0"
        )
        app_name_lbl.pack()

        date_str = datetime.date.today().strftime("%d %B %Y")
        tk.Label(self, text=date_str, font=("Arial", 14), bg="#f0f0f0").pack(anchor="ne", padx=10, pady=(0,5))
        self.clock_lbl = tk.Label(self, font=("Arial", 14), bg="#f0f0f0")
        self.clock_lbl.pack(anchor="ne", padx=10)
        self._update_clock()

        left = tk.Frame(self, bg="#dde")
        left.place(relx=0.02, rely=0.15, relwidth=0.45, relheight=0.83)
        right = tk.Frame(self, bg="#eed")
        right.place(relx=0.52, rely=0.15, relwidth=0.45, relheight=0.83)

        # New Registration panel (droite)
        tk.Label(right, text="New Registration", bg="#bdf", font=("Arial",16)).pack(fill="x")
        tk.Label(right, text="ID (7 digits):", anchor="w").pack(fill="x", padx=20, pady=5)
        self.id_entry = tk.Entry(right)
        self.id_entry.pack(fill="x", padx=20)
        tk.Label(right, text="Name:", anchor="w").pack(fill="x", padx=20, pady=5)
        self.name_entry = tk.Entry(right)
        self.name_entry.pack(fill="x", padx=20)
        self.status_new_lbl = tk.Label(right, text="", fg="green")
        self.status_new_lbl.pack(pady=10)
        tk.Button(right, text="Capture Faces", command=self._on_capture_faces).pack(fill="x", padx=50, pady=5)
        tk.Button(right, text="Train Model", command=self._on_train_model).pack(fill="x", padx=50, pady=5)

        # Attendance panel (gauche)
        tk.Label(left, text="Attendance", bg="#dfb", font=("Arial",16)).pack(fill="x")
        self.tv = ttk.Treeview(left, columns=("Name","Time"), show="tree headings")
        self.tv.heading('#0', text='ID')
        self.tv.heading('Name', text='Name')
        self.tv.heading('Time', text='First Seen')
        self.tv.column('#0', width=80)
        self.tv.column('Name', width=120)
        self.tv.column('Time', width=120)
        self.tv.pack(expand=True, fill="both", padx=10, pady=10)
        self.start_btn = tk.Button(left, text="Start Attendance", command=self._on_start_attendance)
        self.start_btn.pack(fill="x", padx=50, pady=5)

        menubar = tk.Menu(self)
        schedule_menu = tk.Menu(menubar, tearoff=0)
        schedule_menu.add_command(label="Load Schedule", command=self._on_load_schedule)
        menubar.add_cascade(label="Schedule", menu=schedule_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Change Password", command=lambda: self.pwd_mgr.change_password(self))
        help_menu.add_command(label="Forgot Password", command=lambda: self.pwd_mgr.recover_password(self))
        help_menu.add_separator()
        help_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        # Désactiver Start jusqu'à ce que planning chargé
        self._update_start_button_state()

    def _update_clock(self):
        self.clock_lbl.config(text=time.strftime("%H:%M:%S"))
        self.clock_lbl.after(1000, self._update_clock)

    def _on_capture_faces(self):
        user_id = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        success = self.trainer.capture_images(user_id, name)
        if success:
            self.status_new_lbl.config(text=f"Captured images for ID {user_id}", fg="green")
        else:
            self.status_new_lbl.config(text="Capture failed", fg="red")

    def _on_train_model(self):
        # Entraîne LBPH
        self.trainer.train_model("TrainingImageLabel/Trainer.yml", self.status_new_lbl)

    def _on_load_schedule(self):
        path = filedialog.askopenfilename(
            title="Select schedule CSV",
            filetypes=[("CSV files","*.csv"),("All files","*.*")]
        )
        if path:
            try:
                self.schedule_mgr.load_from_csv(path)
                self.schedule_path = path
                self._save_config()
                messagebox.showinfo("Schedule Loaded", "Schedule loaded successfully.")
                self._update_start_button_state()
                # Planifier auto-attendance
                self._schedule_auto_attendance()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load schedule:\n{e}")

    def _update_start_button_state(self):
        # Désactive start si pas de planning
        if self.schedule_mgr.df is None:
            self.start_btn.config(state="disabled")
        else:
            self.start_btn.config(state="normal")

    def _on_start_attendance(self):
        # Manuel, si planning chargé
        if self.schedule_mgr.df is None:
            messagebox.showwarning("No Schedule", "Load a schedule first.")
            return
        self._trigger_attendance_if_in_session()

    def _trigger_attendance_if_in_session(self):
        now = datetime.datetime.now()
        sess = self.schedule_mgr.get_current_session(now)
        if sess is None:
            today_sessions = self.schedule_mgr.get_today_sessions()
            next_info = None
            for s in today_sessions:
                if s['StartTime'] and s['StartTime'] > now.time():
                    next_info = f"Next session today at {s['StartTime'].strftime('%H:%M')}: {s.get('SessionName','')}"
                    break
            if not next_info:
                next_info = "No more sessions today."
            messagebox.showwarning("No Active Session", f"No session is active now.\n{next_info}")
            return
        if sess['status'] == 'break':
            resume = sess['ResumeTime'].strftime("%H:%M")
            messagebox.showinfo("Break Time", f"In break for session \"{sess['SessionName']}\".\nAttendance resumes at {resume}.")
            return
        elif sess['status'] == 'ongoing':
            phase_end = sess['PhaseEnd']
            seconds = self.schedule_mgr.time_until(phase_end, now)
            if seconds < 10:
                messagebox.showwarning("Short Time", "Less than 10 seconds remaining; skipping attendance.")
                return
            messagebox.showinfo("Starting Attendance", f"Recording attendance for \"{sess['SessionName']}\" until {phase_end.strftime('%H:%M')}. It will run automatically.")
            # Lancer dans un thread pour ne pas bloquer l'UI
            threading.Thread(
                target=self.recorder.record_attendance,
                args=(self.tv, self.status_new_lbl, seconds),
                daemon=True
            ).start()

    def _schedule_auto_attendance(self):
        """
        Planifie automatiquement l'appel selon le planning.
        Calcule le prochain démarrage ou déclenche immédiatement si dans session.
        """
        if self.schedule_mgr.df is None:
            return
        now = datetime.datetime.now()
        sess = self.schedule_mgr.get_current_session(now)
        if sess and sess['status'] == 'ongoing':
            self._trigger_attendance_if_in_session()
            phase_end = sess['PhaseEnd']
            end_dt = datetime.datetime.combine(now.date(), phase_end)
            delay = (end_dt - now).total_seconds() + 1
            if delay > 0:
                # re-planifier après la fin de phase
                self.after(int(delay*1000), self._schedule_auto_attendance)
            return
        # Chercher prochain session
        today = now.date()
        next_dt = None
        # Sessions aujourd'hui
        for s in self.schedule_mgr.get_today_sessions():
            if s['StartTime'] and s['StartTime'] > now.time():
                next_dt = datetime.datetime.combine(today, s['StartTime'])
                break
        if next_dt is None:
            # Chercher dans jours suivants
            for day_offset in range(1, 8):
                day = today + datetime.timedelta(days=day_offset)
                df_day = self.schedule_mgr.df[self.schedule_mgr.df['Weekday'] == day.weekday()]
                sessions = []
                for _, row in df_day.iterrows():
                    tm = row.get('StartTime_obj')
                    if tm:
                        sessions.append(tm)
                if sessions:
                    sessions.sort()
                    next_dt = datetime.datetime.combine(day, sessions[0])
                    break
        if next_dt:
            delay = (next_dt - now).total_seconds()
            if delay <= 0:
                delay = 1
            self.after(int(delay*1000), self._schedule_auto_attendance)
