import pandas as pd
import datetime

class ScheduleManager:
    """
    Gère un emploi du temps hebdomadaire chargé depuis un CSV.
    CSV attendu : colonnes Day, SessionName, StartTime, EndTime, BreakStart, BreakEnd
      - Day: weekday name (Monday, Tuesday, ...) ou chiffre 0 (Monday) à 6 (Sunday).
      - StartTime/EndTime: "HH:MM" 24h.
      - BreakStart/BreakEnd: facultatif, "HH:MM" ou vide.
    """

    WEEKDAY_NAME_TO_INT = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    def __init__(self):
        self.df = None  # DataFrame pandas chargé

    def load_from_csv(self, csv_path: str):
        """
        Charge le CSV de planning. Lève ValueError si format incorrect.
        """
        df = pd.read_csv(csv_path)
        # Nettoyage noms de colonnes
        df = df.rename(columns=lambda c: c.strip())
        required = {'Day', 'StartTime', 'EndTime'}
        if not required.issubset(df.columns):
            raise ValueError(f"Schedule CSV must contain columns: {required}")
        # Convertir Day en int 0-6
        def parse_day(val):
            if pd.isna(val):
                return None
            vs = str(val).strip().lower()
            if vs.isdigit():
                i = int(vs)
                if 0 <= i <= 6:
                    return i
            if vs in self.WEEKDAY_NAME_TO_INT:
                return self.WEEKDAY_NAME_TO_INT[vs]
            raise ValueError(f"Invalid Day value: {val}")

        df['Weekday'] = df['Day'].apply(parse_day)

        # Parse times, autoriser "H:M" ou "HH:MM"
        def parse_time(val):
            if pd.isna(val) or not str(val).strip():
                return None
            s = str(val).strip()
            parts = s.split(":")
            if len(parts) == 2:
                try:
                    h = int(parts[0])
                    m = int(parts[1])
                except ValueError:
                    raise ValueError(f"Invalid time value: {val}")
                if 0 <= h < 24 and 0 <= m < 60:
                    return datetime.datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
            raise ValueError(f"Invalid time format (expected H:M or HH:MM): {val}")

        df['StartTime_obj'] = df['StartTime'].apply(parse_time)
        df['EndTime_obj'] = df['EndTime'].apply(parse_time)
        # Breaks facultatifs
        if 'BreakStart' in df.columns and 'BreakEnd' in df.columns:
            df['BreakStart_obj'] = df['BreakStart'].apply(parse_time)
            df['BreakEnd_obj'] = df['BreakEnd'].apply(parse_time)
        else:
            df['BreakStart_obj'] = None
            df['BreakEnd_obj'] = None

        self.df = df

    def get_today_sessions(self):
        """
        Retourne une liste de dicts pour les sessions d'aujourd'hui,
        triées par heure de début.
        Chaque dict:
          {
            'SessionName': str,
            'StartTime': datetime.time,
            'EndTime': datetime.time,
            'BreakStart': datetime.time or None,
            'BreakEnd': datetime.time or None
          }
        """
        if self.df is None:
            return []
        today_weekday = datetime.date.today().weekday()
        df_today = self.df[self.df['Weekday'] == today_weekday]
        sessions = []
        for _, row in df_today.iterrows():
            sessions.append({
                'SessionName': str(row.get('SessionName','')).strip(),
                'StartTime': row['StartTime_obj'],
                'EndTime': row['EndTime_obj'],
                'BreakStart': row.get('BreakStart_obj'),
                'BreakEnd': row.get('BreakEnd_obj')
            })
        sessions.sort(key=lambda s: (s['StartTime'] or datetime.time(0,0)))
        return sessions

    def get_current_session(self, now: datetime.datetime=None):
        """
        Si l'heure courante est dans une session (hors pause), retourne un dict:
          { 'status':'ongoing', 'SessionName':..., 'PhaseEnd':..., 'ResumeTime':... }
        Si dans la pause, retourne:
          { 'status':'break', 'SessionName':..., 'BreakStart':..., 'BreakEnd':..., 'ResumeTime':... }
        Sinon retourne None.
        """
        if self.df is None:
            return None
        if now is None:
            now = datetime.datetime.now()
        today_weekday = now.date().weekday()
        current_time = now.time()
        df_today = self.df[self.df['Weekday'] == today_weekday]
        for _, row in df_today.iterrows():
            st = row['StartTime_obj']
            et = row['EndTime_obj']
            if st is None or et is None:
                continue
            # Si hors intervalle total, sauter
            if current_time < st or current_time >= et:
                continue
            bs = row.get('BreakStart_obj')
            be = row.get('BreakEnd_obj')
            # Si pause définie et on est dans la pause
            if bs and be and bs <= current_time < be:
                return {
                    'status': 'break',
                    'SessionName': str(row.get('SessionName','')).strip(),
                    'BreakStart': bs,
                    'BreakEnd': be,
                    'ResumeTime': be
                }
            # Si hors pause
            if bs and be:
                # Avant la pause
                if st <= current_time < bs:
                    return {
                        'status': 'ongoing',
                        'SessionName': str(row.get('SessionName','')).strip(),
                        'PhaseEnd': bs
                    }
                # Après la pause
                if be <= current_time < et:
                    return {
                        'status': 'ongoing',
                        'SessionName': str(row.get('SessionName','')).strip(),
                        'PhaseEnd': et
                    }
            else:
                # Pas de pause, et dans [st,et)
                return {
                    'status': 'ongoing',
                    'SessionName': str(row.get('SessionName','')).strip(),
                    'PhaseEnd': et
                }
        return None

    def time_until(self, future_time: datetime.time, now: datetime.datetime=None):
        """
        Retourne le nombre de secondes jusqu'à future_time aujourd'hui.
        Si future_time <= now.time(), retourne 0.
        """
        if now is None:
            now = datetime.datetime.now()
        today = now.date()
        dt_future = datetime.datetime.combine(today, future_time)
        delta = (dt_future - now).total_seconds()
        return max(0, delta)
