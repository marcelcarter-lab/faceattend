import os, csv, cv2
import numpy as np
from PIL import Image
import pandas as pd
import tkinter as tk
from tkinter import messagebox

class FaceTrainer:
    """
    Gère la capture de 100 images d’un utilisateur via webcam et l’entraînement LBPH.
    Stocke StudentDetails.csv et range les images dans TrainingImage/{user_id}/.
    """

    def __init__(self, haar_path: str, training_dir: str, details_csv: str):
        self.haar_path = haar_path
        self.training_dir = training_dir
        self.details_csv = details_csv
        os.makedirs(self.training_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.details_csv), exist_ok=True)

    def check_haarcascade(self) -> bool:
        if not os.path.isfile(self.haar_path):
            messagebox.showerror(
                "Missing File",
                f"{self.haar_path} not found. Please place the XML in the folder."
            )
            return False
        return True

    def get_next_serial(self) -> int:
        """
        Retourne le prochain SERIAL NO. pour StudentDetails.csv.
        """
        if not os.path.isfile(self.details_csv):
            return 1
        with open(self.details_csv, newline='') as f:
            reader = csv.reader(f)
            next(reader, None)
            serials = [int(row[0]) for row in reader if row]
        return max(serials, default=0) + 1

    def capture_images(self, user_id: str, name: str) -> bool:
        """
        Capture 100 images du visage de l'utilisateur dans training_dir/{user_id}/.
        Vérifie ID à 7 chiffres et nom alphabétique.
        Met à jour StudentDetails.csv.
        """
        if not self.check_haarcascade():
            return False

        # Vérifier doublon ID dans CSV
        if os.path.isfile(self.details_csv):
            df_ids = pd.read_csv(self.details_csv)
            if user_id in df_ids['ID'].astype(str).tolist():
                messagebox.showerror("Error", f"ID {user_id} already exists.")
                return False

        # ID doit être 7 chiffres
        if not (user_id.isdigit() and len(user_id) == 7):
            messagebox.showerror("Error", "ID must be exactly 7 digits")
            return False

        # Nom uniquement lettres et espaces
        if not name.replace(" ", "").isalpha():
            messagebox.showerror("Error", "Name must contain only letters")
            return False

        serial = self.get_next_serial()
        user_folder = os.path.join(self.training_dir, user_id)
        os.makedirs(user_folder, exist_ok=True)

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            messagebox.showerror("Error", "Unable to open camera")
            return False

        detector = cv2.CascadeClassifier(self.haar_path)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

        count = 0
        total_images = 100
        while count < total_images:
            ret, frame = cam.read()
            if not ret:
                continue
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray_full, scaleFactor=1.1, minNeighbors=6, minSize=(100,100)
            )
            for (x, y, w, h) in faces:
                face_roi = gray_full[y:y+h, x:x+w]
                # Appliquer CLAHE
                face_eq = clahe.apply(face_roi)
                count += 1
                # Nom du fichier: {name}.{serial}.{user_id}.{count}.jpg
                path = os.path.join(user_folder, f"{name}.{serial}.{user_id}.{count}.jpg")
                cv2.imwrite(path, face_eq)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(
                    frame, f"{count}/{total_images}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2
                )
            cv2.imshow("Capturing Faces", frame)
            if cv2.waitKey(50) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

        if count < total_images:
            messagebox.showwarning("Incomplete", f"Only {count} images captured. Please retry.")
            return False

        # Mettre à jour StudentDetails.csv
        header = ["SERIAL NO.", "ID", "NAME"]
        row = [serial, user_id, name]
        if not os.path.isfile(self.details_csv):
            with open(self.details_csv, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(row)
        else:
            with open(self.details_csv, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)

        messagebox.showinfo("Success", f"Captured {total_images} images for ID {user_id}")
        return True

    def train_model(self, model_output_path: str, status_label: tk.Label):
        """
        Entraîne le modèle LBPH sur toutes les images dans training_dir/*/*.jpg.
        Sauvegarde le modèle sous Trainer.yml.
        """
        if not self.check_haarcascade():
            return

        # Créer recognizer LBPH
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            try:
                recognizer = cv2.createLBPHFaceRecognizer()
            except Exception:
                messagebox.showerror(
                    "Error",
                    "LBPHFaceRecognizer not found. Install opencv-contrib-python."
                )
                return

        # Récupérer tous les chemins d'images JPG
        image_paths = []
        for root, _, files in os.walk(self.training_dir):
            for f in files:
                if f.lower().endswith(".jpg"):
                    image_paths.append(os.path.join(root, f))

        faces, ids = [], []
        for img_path in image_paths:
            img = Image.open(img_path).convert("L")
            np_img = np.array(img, "uint8")
            # Le nom du fichier: name.serial.user_id.count.jpg => split par '.'
            parts = os.path.basename(img_path).split(".")
            if len(parts) >= 4:
                # parts[1] est serial (int)
                try:
                    sid = int(parts[1])
                except ValueError:
                    continue
            else:
                continue
            faces.append(np_img)
            ids.append(sid)

        if not faces:
            messagebox.showwarning("No Data", "No images to train. Please register first.")
            return

        recognizer.train(faces, np.array(ids))
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        recognizer.write(model_output_path)
        status_label.config(text="Training completed", fg="green")
