from datetime import datetime, time
import pytz
import logging
from config import *

logger = logging.getLogger(__name__)

# Jam berita besar yang harus dihindari (UTC)
# Update manual atau integrasikan dengan API kalender ekonomi
HIGH_IMPACT_TIMES = [
    # Format: (HH, MM, "Nama Event")
    # Contoh waktu tetap — update tiap minggu
    # (13, 30, "NFP"),
    # (14, 00, "FOMC"),
]

class SessionFilter:
    """Filter trading berdasarkan sesi pasar dan jam berita."""

    def __init__(self):
        self.utc = pytz.utc

    def get_utc_now(self) -> datetime:
        return datetime.now(self.utc)

    def is_london_session(self) -> bool:
        now = self.get_utc_now().time()
        return time(7, 0) <= now <= time(16, 0)

    def is_ny_session(self) -> bool:
        now = self.get_utc_now().time()
        return time(12, 0) <= now <= time(20, 0)

    def is_overlap_session(self) -> bool:
        """London-NY overlap: jam paling aktif dan likuid."""
        now = self.get_utc_now().time()
        return time(12, 0) <= now <= time(16, 0)

    def is_asian_session(self) -> bool:
        """Sesi Asia — hindari untuk scalping (spread lebar, range sempit)."""
        now = self.get_utc_now().time()
        return time(0, 0) <= now < time(7, 0)

    def is_near_high_impact_news(self, buffer_minutes: int = 30) -> tuple:
        """
        Cek apakah dalam rentang waktu berita high impact.
        Return: (bool, nama_event)
        """
        now = self.get_utc_now()
        for hour, minute, name in HIGH_IMPACT_TIMES:
            news_time = now.replace(hour=hour, minute=minute, second=0)
            diff = abs((now - news_time).total_seconds() / 60)
            if diff <= buffer_minutes:
                return True, name
        return False, ""

    def is_friday_close(self) -> bool:
        """Hindari 2 jam sebelum penutupan pasar Jumat (21:00 UTC)."""
        now = self.get_utc_now()
        return now.weekday() == 4 and now.hour >= 19

    def is_monday_open(self) -> bool:
        """Hindari 1 jam pertama pasar Senin (gap risk)."""
        now = self.get_utc_now()
        return now.weekday() == 0 and now.hour < 1

    def can_trade(self) -> tuple:
        """
        Validasi semua kondisi waktu trading.
        Return: (bool, alasan)
        """
        # Jangan trade sesi Asia
        if self.is_asian_session():
            return False, "Sesi Asia — spread lebar, skip"

        # Jangan trade Jumat malam
        if self.is_friday_close():
            return False, "Jumat close — hindari gap akhir pekan"

        # Jangan trade Senin dini hari
        if self.is_monday_open():
            return False, "Senin open — gap risk tinggi"

        # Cek berita besar
        near_news, event_name = self.is_near_high_impact_news()
        if near_news:
            return False, f"Dekat berita {event_name} — trading dihentikan"

        # Harus di sesi London atau NY
        if not (self.is_london_session() or self.is_ny_session()):
            return False, "Di luar jam London & NY"

        # Prioritas: overlap sesi
        session = "OVERLAP ⭐" if self.is_overlap_session() else \
                  "LONDON" if self.is_london_session() else "NEW YORK"
        return True, f"Sesi {session} — trading aktif"
