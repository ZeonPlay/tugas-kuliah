from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")

MATA_KULIAH = [
    "Analisis Kota Cerdas",
    "Jaringan Komputer dan Komunikasi Data",
    "Manajemen Proses Bisnis",
    "Pemrograman Berorientasi Objek",
    "Pemrograman Terstruktur",
    "Rekayasa Perangkat Lunak",
    "Sistem Basis Data",
    "Sistem Operasi",
    "UI/UX Design",
]

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
    palet = tokens["course"]
    if nama not in MATA_KULIAH:
        return tokens["ink_soft"]
    return palet[MATA_KULIAH.index(nama) % len(palet)]


def punya_link(task: dict) -> bool:
    link = (task.get("link_vclass") or "").strip()
    return link.lower().startswith(("http://", "https://"))


def sudah_lewat(task: dict) -> bool:
    return parse_deadline(task["deadline"]) < now_wib()


def build_calendar_events(tasks: list[dict], tokens: dict) -> list[dict]:
    per_tanggal: dict[date, list[dict]] = {}
    for t in tasks:
        d = parse_deadline(t["deadline"]).date()
        per_tanggal.setdefault(d, []).append(t)

    hari_ini = now_wib().date()
    events: list[dict] = []

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
    return [t for t in tasks if sudah_lewat(t)]
