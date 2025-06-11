# faceattend

FaceAttend is a Tkinter-based face recognition attendance application using OpenCV's LBPH algorithm and Haarcascade detector. It supports single-user login with password and recovery phrase, schedule-based automatic attendance tracking, and image capture/training features.

Features

User Authentication: Sign-up with username/password, recovery phrase support, change password.

Face Capture & Training: Capture 100 CLAHE-enhanced images per student into TrainingImage/{ID}/, enforce 7-digit ID and alphabetic name, update StudentDetails/StudentDetails.csv, train LBPH model saved to TrainingImageLabel/Trainer.yml.

Attendance Recording: LBPH-based recognition with Haarcascade face detection; requires continuous detection ≥10 seconds before marking presence; saves daily CSV Attendance/Attendance_YYYY-MM-DD.csv with first-seen time and duration summary.

Schedule Management: Load weekly schedule CSV (Day,SessionName,StartTime,EndTime,BreakStart,BreakEnd), supports H:M or HH:MM formats, auto-triggers attendance when session starts, respects breaks, disables outside sessions.

GUI: Tkinter interface with login/signup window (styled with logo and colors), main window for registration and attendance, menu for loading schedule and password management.
