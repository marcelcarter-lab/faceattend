import os
import json
import bcrypt
import tkinter as tk
from tkinter import messagebox, simpledialog

class PasswordManager:
    """
    Gère un utilisateur unique avec :
      - username
      - mot de passe (haché via bcrypt)
      - recovery_phrase (texte aléatoire affiché une seule fois lors de la configuration)
      - remember_me (optionnel)
    Stocke ces données dans un JSON local.
    """

    def __init__(self, storage_path: str):
        """
        storage_path: chemin vers le JSON, ex. "TrainingImageLabel/credentials.json"
        """
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def is_user_set(self) -> bool:
        """
        Retourne True si le fichier de données existe déjà.
        """
        return os.path.isfile(self.storage_path)

    def _load(self) -> dict:
        """
        Charge et retourne le dictionnaire stocké.
        """
        with open(self.storage_path, "r") as f:
            return json.load(f)

    def _save(self, data: dict):
        """
        Sauvegarde le dictionnaire au format JSON.
        """
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def set_initial_user(self, username: str, password: str):
        """
        Appelé au premier lancement : crée username et mot de passe, génère une recovery phrase.
        Affiche la recovery phrase à l'utilisateur (il doit la conserver).
        """
        # Hash du mot de passe avec bcrypt
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Générer une recovery phrase simple aléatoire : 4 mots hex
        recovery_phrase = " ".join(os.urandom(2).hex() for _ in range(4))

        data = {
            "username": username,
            "password_hash": pw_hash,
            "recovery_phrase": recovery_phrase,
            "remember_me": False
        }
        self._save(data)
        # Afficher la recovery phrase dans un messagebox
        messagebox.showinfo(
            "Account Created",
            "Your account has been created.\n"
            "Please save this recovery phrase somewhere safe:\n\n" +
            recovery_phrase
        )

    def verify_login(self, username: str, password: str) -> bool:
        """
        Vérifie que username et password correspondent aux données stockées.
        """
        try:
            data = self._load()
        except FileNotFoundError:
            return False

        if username != data.get("username", ""):
            return False
        stored_hash = data.get("password_hash", "").encode()
        return bcrypt.checkpw(password.encode(), stored_hash)

    def change_password(self, parent_window=None):
        """
        Fenêtre Tkinter pour changer le mot de passe (après login).
        Demande ancien mot de passe, nouveau + confirmation, puis nouvelle recovery phrase.
        """
        def save():
            old = old_ent.get().strip()
            new = new_ent.get().strip()
            conf = conf_ent.get().strip()

            try:
                data = self._load()
            except Exception:
                messagebox.showerror("Error", "Cannot load credentials.", parent=pwd_win)
                return

            # Vérifier ancien mot de passe
            if not bcrypt.checkpw(old.encode(), data["password_hash"].encode()):
                messagebox.showerror("Error", "Old password incorrect", parent=pwd_win)
                return
            if not new:
                messagebox.showerror("Error", "New password cannot be empty", parent=pwd_win)
                return
            if new != conf:
                messagebox.showerror("Error", "Passwords do not match", parent=pwd_win)
                return

            # Demander nouvelle recovery phrase
            new_recovery = simpledialog.askstring(
                "New Recovery Phrase",
                "Enter a new recovery phrase (store it safely):",
                parent=pwd_win
            )
            if not new_recovery:
                messagebox.showwarning("Cancelled", "No recovery phrase set. Aborting.", parent=pwd_win)
                return

            # Mettre à jour
            new_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
            data["password_hash"] = new_hash
            data["recovery_phrase"] = new_recovery.strip()
            data["remember_me"] = False
            self._save(data)
            messagebox.showinfo("Success", "Password and recovery phrase updated", parent=pwd_win)
            pwd_win.destroy()

        pwd_win = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
        pwd_win.title("Change Password")
        pwd_win.geometry("350x200")
        pwd_win.resizable(False, False)

        tk.Label(pwd_win, text="Old Password:").pack(pady=(15,2))
        old_ent = tk.Entry(pwd_win, show="*")
        old_ent.pack(fill="x", padx=20)

        tk.Label(pwd_win, text="New Password:").pack(pady=(10,2))
        new_ent = tk.Entry(pwd_win, show="*")
        new_ent.pack(fill="x", padx=20)

        tk.Label(pwd_win, text="Confirm New Password:").pack(pady=(10,2))
        conf_ent = tk.Entry(pwd_win, show="*")
        conf_ent.pack(fill="x", padx=20)

        tk.Button(pwd_win, text="Save", command=save).pack(pady=15)

    def recover_password(self, parent_window=None) -> bool:
        """
        Fenêtre pour récupérer/réinitialiser le mot de passe via la recovery phrase.
        Retourne True si reset réussi (pour continuer vers l’app), False sinon.
        """
        if not self.is_user_set():
            messagebox.showwarning("No User", "No user set yet.", parent=parent_window)
            return False

        try:
            data = self._load()
        except Exception:
            messagebox.showerror("Error", "Cannot load credentials.", parent=parent_window)
            return False

        # Demander la recovery phrase
        answer = simpledialog.askstring(
            "Recover Password",
            "Enter your recovery phrase:",
            parent=parent_window
        )
        if not answer or answer.strip() != data.get("recovery_phrase", ""):
            messagebox.showerror("Error", "Incorrect recovery phrase.", parent=parent_window)
            return False

        # Demander nouveau mot de passe
        new = simpledialog.askstring(
            "New Password",
            "Enter a new password:",
            show="*",
            parent=parent_window
        )
        if not new:
            messagebox.showwarning("Cancelled", "No new password set.", parent=parent_window)
            return False
        conf = simpledialog.askstring(
            "Confirm Password",
            "Confirm new password:",
            show="*",
            parent=parent_window
        )
        if new != conf:
            messagebox.showerror("Error", "Passwords do not match.", parent=parent_window)
            return False

        # Demander nouvelle recovery phrase
        new_recovery = simpledialog.askstring(
            "New Recovery Phrase",
            "Enter a new recovery phrase (store it safely):",
            parent=parent_window
        )
        if not new_recovery:
            messagebox.showwarning("Cancelled", "No recovery phrase set. Aborting.", parent=parent_window)
            return False

        # Mettre à jour
        new_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
        data["password_hash"] = new_hash
        data["recovery_phrase"] = new_recovery.strip()
        data["remember_me"] = False
        self._save(data)
        messagebox.showinfo("Success", "Password and recovery phrase have been reset", parent=parent_window)
        return True
