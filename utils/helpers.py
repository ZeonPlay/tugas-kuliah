"""
Konstanta + fungsi bantu: timezone, format tanggal, warna, event kalender.

Fungsi pewarnaan menerima `tokens` (dari utils.styles.get_tokens(dark))
sebagai parameter, bukan konstanta tetap — supaya toggle tema gelap/terang
di sidebar otomatis konsisten di seluruh halaman.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------
# Timezone
# Semua waktu DISIMPAN di database sebagai UTC (kolom timestamptz),
# tapi SELALU ditampilkan dan diinput dalam WIB.
# ---------------------------------------------------------------------
WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")

# ---------------------------------------------------------------------
# Daftar mata kuliah — UBAH DI SINI kalau semester berganti
# ---------------------------------------------------------------------
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
STATUS = ["Belum", "Dikerjakan", "Selesai"]

# Catatan: field prioritas sengaja dihapus dari UI (semua tugas dianggap
# penting; urgensi dilihat dari deadline, bukan dari label buatan admin).
# Kolom `prioritas` di database TETAP ada untuk kompatibilitas — nilainya
# otomatis terisi default 'Sedang' dari sql/setup.sql dan tidak lagi
# ditampilkan atau diminta di form.


# ---------------------------------------------------------------------
# Konversi waktu
# ---------------------------------------------------------------------
def now_wib() -> datetime:
    return datetime.now(WIB)


def parse_deadline(value: str | datetime) -> datetime:
    """String ISO dari Supabase -> datetime aware di zona WIB."""
    if isinstance(value, datetime):
        dt = value
    else:
        teks = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(teks)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(WIB)


def to_utc_iso(tanggal: date, jam: time) -> str:
    """Input form (dianggap WIB) -> string ISO UTC untuk disimpan."""
    lokal = datetime.combine(tanggal, jam).replace(tzinfo=WIB)
    return lokal.astimezone(UTC).isoformat()


def parse_click_date(raw: str) -> date | None:
    """
    Tanggal hasil klik dari streamlit-calendar dikirim sebagai string ISO,
    umumnya dalam UTC (mis. '2025-09-30T17:00:00.000Z' untuk 1 Okt WIB).
    Fungsi ini mengubahnya kembali ke tanggal WIB.
    """
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


# ---------------------------------------------------------------------
# Format tampilan
# ---------------------------------------------------------------------
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
    """
    Return (teks, level). Level: 'lewat' | 'mendesak' (<24 jam) |
    'dekat' (<3 hari) | 'aman'.
    """
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


def warna_status(tokens: dict, status: str) -> str:
    return {
        "Belum": tokens["ink_soft"],
        "Dikerjakan": tokens["near"],
        "Selesai": tokens["safe"],
    }.get(status, tokens["ink_soft"])


def punya_link(task: dict) -> bool:
    link = (task.get("link_vclass") or "").strip()
    return link.lower().startswith(("http://", "https://"))


def sudah_lewat(task: dict) -> bool:
    return parse_deadline(task["deadline"]) < now_wib()


# ---------------------------------------------------------------------
# Kalender
# ---------------------------------------------------------------------
def build_calendar_events(tasks: list[dict], tokens: dict) -> list[dict]:
    """
    Satu event RINGKASAN per tanggal ("1 deadline" / "2 deadline"), bukan
    satu event per tugas. Ini sengaja: kalau ada banyak tugas menumpuk di
    satu tanggal, chip individual jadi kecil-kecil dan susah diklik —
    dengan satu blok ringkasan, seluruh sel tanggal jadi target klik yang
    besar, lalu detailnya dibaca di daftar di bawah kalender.
    """
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
    """Tugas yang belum selesai dan deadline-nya belum lewat."""
    sekarang = now_wib()
    kandidat = [t for t in tasks if t.get("status") != "Selesai" and parse_deadline(t["deadline"]) >= sekarang]
    kandidat.sort(key=lambda t: parse_deadline(t["deadline"]))
    return kandidat[:jumlah]


def tugas_terlewat(tasks: list[dict]) -> list[dict]:
    """Tugas yang deadline-nya sudah lewat tapi belum ditandai selesai —
    dipakai untuk pengingat di halaman utama."""
    return [t for t in tasks if t.get("status") != "Selesai" and sudah_lewat(t)]
