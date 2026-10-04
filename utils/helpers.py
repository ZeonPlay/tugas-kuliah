import hashlib
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")


JENIS = ["Praktikum", "Teori", "Quiz", "Ujian"]


def now_wib() -> datetime:
    return datetime.now(WIB)


def parse_deadline(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        teks = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(teks)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(WIB)


def to_utc_iso(tanggal: date, jam: time) -> str:
    lokal = datetime.combine(tanggal, jam).replace(tzinfo=WIB)
    return lokal.astimezone(UTC).isoformat()


def parse_click_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        teks = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(teks)
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(WIB).date()


HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = [
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


def format_tanggal(d: date) -> str:
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"


def format_deadline(value: str | datetime) -> str:
    dt = parse_deadline(value)
    return f"{format_tanggal(dt.date())} • {dt:%H:%M} WIB"


def sisa_waktu(value: str | datetime) -> tuple[str, str]:
    dt = parse_deadline(value)
    selisih = dt - now_wib()
    detik = selisih.total_seconds()

    if detik < 0:
        return "Sudah lewat", "lewat"

    if detik < 3600:
        return f"{int(detik // 60)} menit lagi", "mendesak"
    if detik < 86400:
        return f"{int(detik // 3600)} jam lagi", "mendesak"

    hari = int(detik // 86400)
    level = "dekat" if hari < 3 else "aman"
    return f"{hari} hari lagi", level


def warna_urgensi(tokens: dict, level: str) -> str:
    return {
        "lewat": tokens["urgent"],
        "mendesak": tokens["urgent"],
        "dekat": tokens["near"],
        "aman": tokens["ink_soft"],
    }.get(level, tokens["ink_soft"])


def warna_matkul(tokens: dict, nama: str) -> str:
    """Beri warna konsisten untuk nama mata kuliah tanpa daftar hardcoded."""
    palet = tokens["course"]
    if not nama or not palet:
        return tokens["ink_soft"]

    # hashlib dipakai agar hasil tetap sama antar-restart aplikasi.
    indeks = int(hashlib.sha256(str(nama).encode("utf-8")).hexdigest()[:8], 16) % len(palet)
    return palet[indeks]


def punya_link(task: dict) -> bool:
    link = (task.get("link_vclass") or "").strip()
    return link.lower().startswith(("http://", "https://"))


def sudah_lewat(task: dict) -> bool:
    return parse_deadline(task["deadline"]) < now_wib()


def build_calendar_events(tasks: list[dict], tokens: dict) -> list[dict]:
    per_tanggal: dict[date, list[dict]] = {}
    for task in tasks:
        d = parse_deadline(task["deadline"]).date()
        per_tanggal.setdefault(d, []).append(task)

    hari_ini = now_wib().date()
    events: list[dict] = []

    # Tampilan Bulan tetap ringkas: satu event per tanggal yang hanya
    # menunjukkan jumlah deadline pada hari tersebut.
    for d, daftar in sorted(per_tanggal.items()):
        jumlah = len(daftar)
        warna = tokens["ink_soft"] if d < hari_ini else tokens["urgent"]
        events.append(
            {
                "start": d.isoformat(),
                "end": (d + timedelta(days=1)).isoformat(),
                "allDay": True,
                "title": f"{jumlah} deadline",
                "backgroundColor": warna,
                "borderColor": warna,
                "textColor": "#FFFFFF",
                "classNames": ["calendar-summary-event"],
            }
        )

    # Event individual hanya muncul pada tampilan Daftar.
    for task in sorted(tasks, key=lambda item: parse_deadline(item["deadline"])):
        deadline = parse_deadline(task["deadline"])
        _, level = sisa_waktu(task["deadline"])
        warna = warna_urgensi(tokens, level)
        course = task.get("mata_kuliah") or "Tanpa Mata Kuliah"
        judul = task.get("judul") or "Tugas tanpa judul"

        events.append(
            {
                "start": deadline.isoformat(),
                "allDay": False,
                "display": "list-item",
                "title": f"{judul} · {course}",
                "backgroundColor": warna,
                "borderColor": warna,
                "textColor": "#FFFFFF",
                "classNames": ["calendar-task-event"],
                "extendedProps": {
                    "task_id": task.get("id"),
                    "mata_kuliah": course,
                },
            }
        )

    return events


def tasks_pada_tanggal(tasks: list[dict], target: date) -> list[dict]:
    hasil = [t for t in tasks if parse_deadline(t["deadline"]).date() == target]
    hasil.sort(key=lambda t: parse_deadline(t["deadline"]))
    return hasil


def deadline_terdekat(tasks: list[dict], jumlah: int = 5) -> list[dict]:
    sekarang = now_wib()
    kandidat = [t for t in tasks if parse_deadline(t["deadline"]) >= sekarang]
    kandidat.sort(key=lambda t: parse_deadline(t["deadline"]))
    return kandidat[:jumlah]


def tugas_terlewat(tasks: list[dict]) -> list[dict]:
    """Semua tugas yang deadline-nya sudah lewat."""
    return [t for t in tasks if sudah_lewat(t)]


def tugas_baru_terlewat(tasks: list[dict], hari: int = 3) -> list[dict]:
    """Tugas yang deadline-nya lewat dalam N hari terakhir."""
    sekarang = now_wib()
    batas = sekarang - timedelta(days=hari)
    hasil = [
        t for t in tasks
        if batas <= parse_deadline(t["deadline"]) < sekarang
    ]
    hasil.sort(key=lambda t: parse_deadline(t["deadline"]), reverse=True)
    return hasil
