import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

class PasswordManager:
    """
    Gère la création, vérification et récupération du mot de passe
    pour un utilisateur unique de l’application.
    Le JSON stocké aura la forme :
      {
        "username": "alice",
        "password": "Secret123",
        "recovery": "maPhraseSecrète",
        "remember_me": False
      }
    """

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def is_user_set(self) -> bool:
        return os.path.isfile(self.storage_path)

    def load_data(self) -> dict:
        with open(self.storage_path, "r") as f:
            return json.load(f)

    def save_data(self, data: dict):
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def set_initial_user(self, username: str, password: str, recovery_phrase: str, remember_me: bool):
        data = {
            "username": username,
            "password": password,
            "recovery": recovery_phrase,
            "remember_me": remember_me
        }
        self.save_data(data)

    def verify_login(self, username: str, password: str) -> bool:
        """
        Vérifie que username et password correspondent à ceux stockés.
        """
        data = self.load_data()
        return (username == data.get("username", "") and
                password == data.get("password", ""))

    def change_password(self):
        """
        Fenêtre pour changer le mot de passe (après login).
        L'utilisateur entre l'ancien mot de passe, puis le nouveau + recovery.
        (On ne peut pas changer le username via cette boîte.)
        """
        def save():
            old_val = old_ent.get().strip()
            new_val = new_ent.get().strip()
            conf_val = conf_ent.get().strip()

            data = self.load_data()
            current_pass = data.get("password", "")

            if old_val != current_pass:
                messagebox.showerror("Error", "Old password incorrect")
                return
            if not new_val or new_val != conf_val:
                messagebox.showerror("Error", "New passwords do not match or are empty")
                return

            new_recovery = simpledialog.askstring(
                "Recovery Phrase",
                "Enter a new recovery phrase:",
                show=None
            )
            if not new_recovery:
                messagebox.showwarning("Cancelled", "No recovery phrase set. Aborting.")
                return

            data["password"] = new_val
            data["recovery"] = new_recovery
            self.save_data(data)
            messagebox.showinfo("Success", "Password and recovery phrase updated")
            pwd_win.destroy()

        pwd_win = tk.Toplevel()
        pwd_win.title("Change Password")
        pwd_win.geometry("350x220")
        pwd_win.resizable(False, False)

        tk.Label(pwd_win, text="Old Password:", anchor="w").pack(fill="x", padx=20, pady=(15,2))
        old_ent = tk.Entry(pwd_win, show="*")
        old_ent.pack(fill="x", padx=20)

        tk.Label(pwd_win, text="New Password:", anchor="w").pack(fill="x", padx=20, pady=(10,2))
        new_ent = tk.Entry(pwd_win, show="*")
        new_ent.pack(fill="x", padx=20)

        tk.Label(pwd_win, text="Confirm New Password:", anchor="w").pack(fill="x", padx=20, pady=(10,2))
        conf_ent = tk.Entry(pwd_win, show="*")
        conf_ent.pack(fill="x", padx=20)

        tk.Button(pwd_win, text="Save", width=10, command=save).pack(pady=15)

    def recover_password(self) -> bool:
        """
        Fenêtre pour récupérer / réinitialiser le mot de passe via la phrase secrète.
        Retourne True si la réinitialisation a eu lieu, False sinon.
        """
        if not self.is_user_set():
            messagebox.showwarning("No User", "No user has been set yet.")
            return False

        data = self.load_data()
        current_recovery = data.get("recovery", "")

        answer = simpledialog.askstring("Forgot Password", "Enter your recovery phrase:")
        if not answer or answer.strip() != current_recovery:
            messagebox.showerror("Error", "Recovery phrase incorrect.")
            return False

        new_pass = simpledialog.askstring("New Password", "Enter your new password:", show="*")
        if not new_pass:
            messagebox.showwarning("Cancelled", "No new password set.")
            return False

        confirm_pass = simpledialog.askstring("Confirm Password", "Confirm your new password:", show="*")
        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match.")
            return False

        new_recovery = simpledialog.askstring("New Recovery Phrase", "Enter a new recovery phrase:")
        if not new_recovery:
            messagebox.showwarning("Cancelled", "No recovery phrase set. Aborting.")
            return False

        data["password"] = new_pass.strip()
        data["recovery"] = new_recovery.strip()
        self.save_data(data)
        messagebox.showinfo("Success", "Password and recovery phrase have been reset")
        return True
