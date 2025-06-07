import os, csv, cv2, time, datetime
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class AttendanceRecorder:
    """
    Gère la prise d’appel automatique pendant 60s, la reconnaissance des visages
    à l’aide du modèle LBPH entraîné, et la sauvegarde dans un CSV.
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

    def record_attendance(self, treeview: ttk.Treeview, status_label: tk.Label):
        """
        Lance la session de reconnaissance faciale pendant 60s.
        Affiche les ID reconnus dans le Treeview et écrit dans Attendance/YYYY-MM-DD.csv.
        """
        if not self.check_haarcascade():
            return

        if not os.path.isfile(self.model_path):
            messagebox.showerror("Error", "Training data missing")
            return

        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            try:
                recognizer = cv2.createLBPHFaceRecognizer()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
        recognizer.read(self.model_path)

        df = pd.read_csv(self.details_csv)
        detector = cv2.CascadeClassifier(self.haar_path)
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            messagebox.showerror("Error", "Unable to open camera")
            return

        font = cv2.FONT_HERSHEY_SIMPLEX
        today = datetime.date.today().strftime("%Y-%m-%d")
        attendance_dir = "Attendance"
        os.makedirs(attendance_dir, exist_ok=True)
        attendance_file = f"{attendance_dir}/Attendance_{today}.csv"

        if not os.path.isfile(attendance_file):
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID","NAME","DATE","TIME"])

        for itm in treeview.get_children():
            treeview.delete(itm)

        presence_times = {}
        start_time = time.time()
        duration = 60

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break

            ret, frame = cam.read()
            if not ret:
                continue
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clahe_full = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray_eq = clahe_full.apply(gray_full)

            faces = detector.detectMultiScale(
                gray_eq, scaleFactor=1.1, minNeighbors=5, minSize=(80,80)
            )
            for (x, y, w, h) in faces:
                face_roi = gray_eq[y:y+h, x:x+w]
                sid, conf = recognizer.predict(face_roi)
                if conf < 70:
                    row = df[df["SERIAL NO."] == sid].iloc[0]
                    id_str, name_str = row["ID"], row["NAME"]
                    tstamp = datetime.datetime.now().strftime("%H:%M:%S")

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(frame, name_str, (x, y+h+25),
                                font, 0.8, (0,255,0), 2, cv2.LINE_AA)

                    if id_str not in presence_times:
                        presence_times[id_str] = tstamp
                        with open(attendance_file, "a", newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([id_str, name_str, today, tstamp])
                        treeview.insert("", "end", text=id_str, values=(name_str, tstamp))
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
                    cv2.putText(frame, "Unknown", (x, y+h+25),
                                font, 0.8, (0,0,255), 2, cv2.LINE_AA)

            cv2.imshow("Taking Attendance (60s)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

        stop_time = datetime.datetime.now()
        with open(attendance_file, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([])
            writer.writerow(["ID","DURATION_SECONDS"])
            for id_str, first_seen in presence_times.items():
                fmt = "%H:%M:%S"
                start_dt = datetime.datetime.strptime(f"{today} {first_seen}", f"%Y-%m-%d {fmt}")
                secs = int((stop_time - start_dt).total_seconds())
                writer.writerow([id_str, secs])

        status_label.config(text="Attendance recorded", fg="green")
