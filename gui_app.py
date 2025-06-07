import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import time
from pathlib import Path
from PIL import Image, ImageTk

from password_manager import PasswordManager
from face_trainer import FaceTrainer
from attendance_recorder import AttendanceRecorder

class FaceAttendanceApp(tk.Tk):
    """
    Interface principale avec :
      - Logo et nom de l'app (“FaceAttend”) en haut de la fenêtre.
      - Fenêtre de login stylée en deux volets (volet bleu à gauche, volet blanc à droite).
      - Si pas de compte existant → formulaire Sign Up.
      - Sinon → formulaire Login avec “Remember me” + “Forgot your password?”.
      - Après connexion, la fenêtre de login disparaît et l’application principale apparaît.
    """

    def __init__(self):
        super().__init__()
        self.title("FaceAttend")
        self.geometry("1000x600")
        self.configure(bg="#f0f0f0")

        # ─── Définir le chemin vers le logo ───
        # Placez "attandance_logo.png" dans le même dossier que ce fichier.
        self.logo_path = Path(__file__).parent / "attandance_logo.png"

        # Charger l'icône de la fenêtre (favicon) depuis le même logo, si possible.
        if self.logo_path.exists():
            try:
                icon_img = tk.PhotoImage(file=str(self.logo_path))
                self.iconphoto(False, icon_img)
            except tk.TclError:
                pass  # Si échec, on ignore

        # Instancier les gestionnaires : mot de passe, trainer, recorder
        self.pwd_mgr = PasswordManager("TrainingImageLabel/psd_info.json")
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

        # Construire et masquer l'interface principale
        self._build_main_interface()
        self.withdraw()

        # Ouvrir la fenêtre de login stylée
        self._create_login_window()

    def _create_login_window(self):
        """
        Crée la fenêtre Toplevel pour le login en deux volets :
          - Volet gauche bleu (#4A90E2) avec un petit logo (60×60) au coin supérieur gauche.
          - Volet droit blanc avec les champs Sign Up / Login.
        """
        self.login_win = tk.Toplevel(self)
        self.login_win.title("FaceAttend – Login")
        self.login_win.geometry("750x400")
        self.login_win.resizable(False, False)
        self.login_win.configure(bg="#ffffff")
        # Si l'utilisateur ferme la fenêtre de login, on quitte l'application
        self.login_win.protocol("WM_DELETE_WINDOW", self.destroy)

        # Centrer la fenêtre 750×400
        w = 750
        h = 400
        x = (self.login_win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.login_win.winfo_screenheight() // 2) - (h // 2)
        self.login_win.geometry(f"{w}x{h}+{x}+{y}")

        # ───────────────────────────
        # VOLET GAUCHE : fond bleu #
        # ───────────────────────────
        left_frame = tk.Frame(self.login_win, bg="#4A90E2", width=300, height=400)
        left_frame.pack(side="left", fill="y")

        # Charger et redimensionner le logo en 60×60
        if self.logo_path.exists():
            try:
                raw_logo = Image.open(self.logo_path)
                small_logo = raw_logo.resize((60, 60), Image.ANTIALIAS)
                # Stocker dans un attribut pour que PhotoImage ne soit pas garbage-collected
                self.login_logo_img = ImageTk.PhotoImage(small_logo)
                logo_lbl = tk.Label(left_frame, image=self.login_logo_img, bg="#4A90E2")
                # Placer dans le coin supérieur gauche, avec 10px de marge
                logo_lbl.place(x=10, y=10)
            except Exception:
                pass  # Si échec de chargement du logo, on continue sans image

        # Texte de bienvenue sous (ou à côté) du logo
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

        # ─────────────────────────────────────────
        # VOLET DROIT : fond blanc (Sign Up / Login) #
        # ─────────────────────────────────────────
        right_frame = tk.Frame(self.login_win, bg="#ffffff", width=450, height=400)
        right_frame.pack(side="right", fill="both", expand=True)

        form_font = ("Helvetica", 11)
        entry_font = ("Helvetica", 11)
        btn_font = ("Helvetica", 11, "bold")

        if not self.pwd_mgr.is_user_set():
            # --- FORMULAIRE Sign Up ---
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

            tk.Label(right_frame, text="Recovery Phrase", font=form_font, bg="#ffffff").place(x=30, y=275)
            self.recovery_ent = tk.Entry(right_frame, font=entry_font)
            self.recovery_ent.place(x=30, y=300, width=280, height=25)

            tk.Button(
                right_frame,
                text="Create Account",
                font=btn_font,
                bg="#4A90E2",
                fg="#ffffff",
                activebackground="#357ABD",
                command=self._on_create_user
            ).place(x=30, y=345, width=280, height=30)

        else:
            # --- FORMULAIRE Login ---
            data = self.pwd_mgr.load_data()
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

            # Checkbox "Remember me"
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

            # Lien "Forgot your password?"
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
        """
        Création initiale : on récupère username, password, confirm, recovery,
        on coche “Remember me” par défaut, puis on ouvre l’app principale.
        """
        username = self.new_user_ent.get().strip()
        pw = self.new_pass_ent.get().strip()
        conf = self.confirm_pass_ent.get().strip()
        rec = self.recovery_ent.get().strip()
        remember_me = True  # coché par défaut

        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        if not pw:
            messagebox.showerror("Error", "Password cannot be empty.")
            return
        if pw != conf:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if not rec:
            messagebox.showerror("Error", "Recovery phrase cannot be empty.")
            return

        self.pwd_mgr.set_initial_user(username, pw, rec, remember_me)
        messagebox.showinfo("Success", "Account created successfully.")

        self.login_win.destroy()
        self.deiconify()

    def _on_verify_login(self):
        """
        Vérifie username + password. Si OK, on met à jour 'remember_me' et on ouvre l’appli.
        Sinon, propose la récupération.
        """
        username = self.login_user_ent.get().strip()
        pw = self.login_pass_ent.get().strip()

        if self.pwd_mgr.verify_login(username, pw):
            data = self.pwd_mgr.load_data()
            data["remember_me"] = self.remember_var.get()
            if data["remember_me"]:
                data["username"] = username
            else:
                data["username"] = ""
            self.pwd_mgr.save_data(data)

            self.login_win.destroy()
            self.deiconify()
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
        """
        Lance la procédure de récupération depuis la fenêtre de login.
        Si réussite, on ferme login_win et on ouvre l’appli.
        """
        success = self.pwd_mgr.recover_password()
        if success:
            self.login_win.destroy()
            self.deiconify()

    def _build_main_interface(self):
        # ─── HEADER AVEC NOM DE L’APP ───
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

        # ─── DATE & HORLOGE EN HAUT À DROITE ───
        date_str = datetime.date.today().strftime("%d %B %Y")
        tk.Label(self, text=date_str, font=("Arial", 14), bg="#f0f0f0").pack(anchor="ne", padx=10, pady=(0,5))
        self.clock_lbl = tk.Label(self, font=("Arial", 14), bg="#f0f0f0")
        self.clock_lbl.pack(anchor="ne", padx=10)
        self._update_clock()

        # ─── PANNEAUX PRINCIPAUX ───
        left = tk.Frame(self, bg="#dde")
        left.place(relx=0.02, rely=0.15, relwidth=0.45, relheight=0.83)
        right = tk.Frame(self, bg="#eed")
        right.place(relx=0.52, rely=0.15, relwidth=0.45, relheight=0.83)

        # Panneau “New Registration” (droite)
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

        # Panneau “Attendance” (gauche)
        tk.Label(left, text="Attendance (auto 60s)", bg="#dfb", font=("Arial",16)).pack(fill="x")
        self.tv = ttk.Treeview(left, columns=("Name","Time"), show="tree headings")
        self.tv.heading('#0', text='ID')
        self.tv.heading('Name', text='Name')
        self.tv.heading('Time', text='First Seen')
        self.tv.column('#0', width=80)
        self.tv.column('Name', width=120)
        self.tv.column('Time', width=120)
        self.tv.pack(expand=True, fill="both", padx=10, pady=10)
        tk.Button(left, text="Start Attendance", command=self._on_start_attendance).pack(
            fill="x", padx=50, pady=5
        )

        # Barre de menu (Change Password, Forgot Password, Exit)
        menubar = tk.Menu(self)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Change Password", command=self.pwd_mgr.change_password)
        help_menu.add_command(label="Forgot Password", command=self.pwd_mgr.recover_password)
        help_menu.add_separator()
        help_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

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
        # L’utilisateur est déjà authentifié → pas de nouvelle demande de mot de passe ici
        self.trainer.train_model("TrainingImageLabel/Trainer.yml", self.status_new_lbl)

    def _on_start_attendance(self):
        self.recorder.record_attendance(self.tv, self.status_new_lbl)
