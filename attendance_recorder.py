import os, csv, cv2, time, datetime
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class AttendanceRecorder:
    """
    Gère la prise d’appel automatique pendant une durée paramétrée (par défaut 60s),
    la reconnaissance LBPH et la sauvegarde dans un CSV daily.
    Ne marque “présent” qu’après MIN_PRESENT_SECONDS depuis la première détection.
    """

    def __init__(self, haar_path: str, model_path: str, details_csv: str):
        self.haar_path = haar_path
        self.model_path = model_path
        self.details_csv = details_csv
        os.makedirs(os.path.dirname(self.details_csv), exist_ok=True)

    def check_haarcascade(self) -> bool:
        if not os.path.isfile(self.haar_path):
            messagebox.showerror(
                "Missing File",
                f"{self.haar_path} not found."
            )
            return False
        return True

    def record_attendance(self, treeview: ttk.Treeview, status_label: tk.Label, duration: float = 60):
        """
        Lance la session de reconnaissance faciale pendant `duration` secondes.
        Affiche les ID reconnus dans le Treeview et écrit dans Attendance/YYYY-MM-DD.csv
        seulement si chaque étudiant est détecté au moins MIN_PRESENT_SECONDS.
        """
        if not self.check_haarcascade():
            return

        if not os.path.isfile(self.model_path):
            messagebox.showerror("Error", "Training data missing", parent=status_label)
            return

        # Charger recognizer LBPH
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            try:
                recognizer = cv2.createLBPHFaceRecognizer()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=status_label)
                return
        recognizer.read(self.model_path)

        # Charger les détails étudiants
        try:
            df = pd.read_csv(self.details_csv)
        except Exception:
            messagebox.showerror("Error", "Cannot load StudentDetails.csv", parent=status_label)
            return

        detector = cv2.CascadeClassifier(self.haar_path)
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            messagebox.showerror("Error", "Unable to open camera", parent=status_label)
            return

        font = cv2.FONT_HERSHEY_SIMPLEX
        today = datetime.date.today().strftime("%Y-%m-%d")
        attendance_dir = "Attendance"
        os.makedirs(attendance_dir, exist_ok=True)
        attendance_file = f"{attendance_dir}/Attendance_{today}.csv"

        # Créer le CSV avec header si nouveau
        if not os.path.isfile(attendance_file):
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID","NAME","DATE","TIME"])

        # Vider Treeview
        for itm in treeview.get_children():
            treeview.delete(itm)

        # Structures pour logique de seuil
        presence_times = {}    # { id_str: datetime_of_first_detection }
        marked_present = set() # IDs déjà marqués présent

        start_time = time.time()
        status_label.config(text="Recording attendance...", fg="black")

        MIN_PRESENT_SECONDS = 10  # seuil minimal avant de marquer présent

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            ret, frame = cam.read()
            if not ret:
                continue
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray_full, scaleFactor=1.1, minNeighbors=6, minSize=(100,100)
            )

            now = datetime.datetime.now()

            for (x, y, w, h) in faces:
                face_roi = gray_full[y:y+h, x:x+w]
                sid, conf = recognizer.predict(face_roi)
                # Ajustez threshold de confiance si besoin
                if conf < 70:
                    # Visage reconnu
                    row = df[df["SERIAL NO."] == sid]
                    if row.empty:
                        continue
                    row0 = row.iloc[0]
                    id_str, name_str = row0["ID"], row0["NAME"]

                    # Dessiner rectangle vert + nom
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(frame, name_str, (x, y+h+25),
                                font, 0.8, (0,255,0), 2, cv2.LINE_AA)

                    # Si première détection pour cet ID, mémoriser heure
                    if id_str not in presence_times:
                        presence_times[id_str] = now
                    else:
                        first_seen = presence_times[id_str]
                        seconds_seen = (now - first_seen).total_seconds()
                        if seconds_seen >= MIN_PRESENT_SECONDS and id_str not in marked_present:
                            # Marquer présent
                            tstamp = first_seen.strftime("%H:%M:%S")
                            with open(attendance_file, "a", newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow([id_str, name_str, today, tstamp])
                            treeview.insert("", "end", text=id_str, values=(name_str, tstamp))
                            marked_present.add(id_str)
                else:
                    # Visage non reconnu
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
                    cv2.putText(frame, "Unknown", (x, y+h+25),
                                font, 0.8, (0,0,255), 2, cv2.LINE_AA)

            cv2.imshow("Taking Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

        # Écrire résumé des durées pour ceux marqués présent
        stop_time = datetime.datetime.now()
        with open(attendance_file, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([])
            writer.writerow(["ID","DURATION_SECONDS"])
            for id_str in marked_present:
                first_seen = presence_times.get(id_str)
                if first_seen:
                    secs = int((stop_time - first_seen).total_seconds())
                    writer.writerow([id_str, secs])

        status_label.config(text="Attendance recorded", fg="green")
