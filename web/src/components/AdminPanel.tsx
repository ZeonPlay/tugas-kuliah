import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { supabase, supabaseConfigMissing } from "../lib/supabase";
import { normalizeLegacyMarkdown } from "./MarkdownContent";
import MarkdownEditor from "./MarkdownEditor";

type Task = {
  id: string;
  judul: string;
  mata_kuliah: string;
  jenis: string;
  deadline: string;
  ketentuan: string | null;
  link_vclass: string | null;
  link_pengumpulan: string | null;
  file_soal: string | null;
};

type Course = {
  id: string;
  nama: string;
  semester: number;
  kategori: string;
  aktif: boolean;
};

type AdminPanelProps = {
  tasks: Task[];
  courses: Course[];
  onBack: () => void;
  onDataChanged: () => void;
};

type AccessState = "none" | "checking" | "allowed" | "denied" | "error";
type AuthMode = "login" | "signup";
type TaskDraft = {
  judul: string;
  mata_kuliah: string;
  jenis: string;
  deadlineDate: string;
  deadlineTime: string;
  ketentuan: string;
  link_vclass: string;
  link_pengumpulan: string;
  file: File | null;
  removeCurrentFile: boolean;
};

const TASK_TYPES = ["Teori", "Praktikum", "Quiz", "Ujian"];
const ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "docx", "zip"];
const MAX_FILE_BYTES = 10 * 1024 * 1024;

function wibDateInput(value?: string): string {
  const date = value ? new Date(value) : new Date();
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const part = (type: string) => parts.find((item) => item.type === type)?.value ?? "";
  return part("year") + "-" + part("month") + "-" + part("day");
}

function wibTimeInput(value?: string): string {
  const date = value ? new Date(value) : new Date();
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Jakarta",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const part = (type: string) => parts.find((item) => item.type === type)?.value ?? "00";
  return part("hour") + ":" + part("minute");
}

function initialDraft(task: Task | null, courses: Course[]): TaskDraft {
  return {
    judul: task?.judul ?? "",
    mata_kuliah: task?.mata_kuliah ?? courses[0]?.nama ?? "",
    jenis: task?.jenis ?? "Teori",
    deadlineDate: wibDateInput(task?.deadline),
    deadlineTime: task ? wibTimeInput(task.deadline) : "23:59",
    ketentuan: normalizeLegacyMarkdown(task?.ketentuan ?? ""),
    link_vclass: task?.link_vclass ?? "",
    link_pengumpulan: task?.link_pengumpulan ?? "",
    file: null,
    removeCurrentFile: false,
  };
}

function safeHttpUrl(value: string): boolean {
  if (!value.trim()) return true;
  try {
    const parsed = new URL(value.trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function storagePathFromUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const pathname = new URL(value).pathname;
    const marker = "/storage/v1/object/public/task-files/";
    const index = pathname.indexOf(marker);
    if (index < 0) return null;
    return decodeURIComponent(pathname.slice(index + marker.length));
  } catch {
    return null;
  }
}

async function checkAdminAllowlist(email: string): Promise<{ allowed: boolean; error: string | null }> {
  if (!supabase) return { allowed: false, error: "Supabase belum dikonfigurasi." };
  const { data, error } = await supabase
    .from("admin_users")
    .select("email")
    .eq("email", email)
    .maybeSingle();

  if (error) {
    return {
      allowed: false,
      error: "Daftar admin tidak bisa diperiksa. Pastikan tabel admin_users mengizinkan pembacaan email untuk proses verifikasi.",
    };
  }
  return { allowed: Boolean(data), error: null };
}

function TaskForm({
  task,
  courses,
  onCancel,
  onSaved,
}: {
  task: Task | null;
  courses: Course[];
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<TaskDraft>(() => initialDraft(task, courses));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState("");
  const [saving, setSaving] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  function change<K extends keyof TaskDraft>(key: K, value: TaskDraft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
    setErrors((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
    setSubmitError("");
  }

  function validate(): Record<string, string> {
    const next: Record<string, string> = {};
    if (!draft.judul.trim()) next.judul = "Judul tugas wajib diisi.";
    else if (draft.judul.trim().length < 3) next.judul = "Judul terlalu pendek; isi minimal 3 karakter.";
    else if (draft.judul.trim().length > 180) next.judul = "Judul maksimal 180 karakter.";
    if (!draft.mata_kuliah) next.mata_kuliah = "Pilih mata kuliah terlebih dahulu.";
    if (!TASK_TYPES.includes(draft.jenis)) next.jenis = "Pilih jenis tugas yang tersedia.";
    if (!draft.deadlineDate) next.deadlineDate = "Tanggal deadline wajib diisi.";
    if (!draft.deadlineTime) next.deadlineTime = "Jam deadline wajib diisi.";
    if (draft.deadlineDate && draft.deadlineTime) {
      const deadline = new Date(draft.deadlineDate + "T" + draft.deadlineTime + ":00+07:00");
      if (Number.isNaN(deadline.getTime())) next.deadlineDate = "Tanggal atau jam deadline tidak valid.";
    }
    if (!safeHttpUrl(draft.link_vclass)) next.link_vclass = "Masukkan URL yang diawali http:// atau https://.";
    if (!safeHttpUrl(draft.link_pengumpulan)) next.link_pengumpulan = "Masukkan URL yang diawali http:// atau https://.";
    if (draft.file) {
      const ext = draft.file.name.split(".").pop()?.toLowerCase() ?? "";
      if (!ALLOWED_EXTENSIONS.includes(ext)) next.file = "Format lampiran yang diizinkan: PDF, PNG, JPG, DOCX, atau ZIP.";
      else if (draft.file.size > MAX_FILE_BYTES) next.file = "Ukuran lampiran maksimal 10 MB.";
    }
    return next;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError("");
    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setSubmitError("Periksa kolom yang ditandai sebelum menyimpan.");
      window.requestAnimationFrame(() => {
        document.querySelector<HTMLElement>(".admin-form [aria-invalid='true']")?.focus();
      });
      return;
    }
    if (!supabase) {
      setSubmitError("Supabase belum dikonfigurasi.");
      return;
    }

    setSaving(true);
    let uploadedPath: string | null = null;
    try {
      let newFileUrl: string | null = null;
      if (draft.file) {
        const ext = draft.file.name.split(".").pop()?.toLowerCase().replace(/[^a-z0-9]/g, "") ?? "bin";
        uploadedPath = crypto.randomUUID() + "." + ext;
        const { error: uploadError } = await supabase.storage
          .from("task-files")
          .upload(uploadedPath, draft.file, {
            upsert: false,
            contentType: draft.file.type || "application/octet-stream",
          });
        if (uploadError) throw new Error("Lampiran gagal diunggah. Periksa izin Storage dan coba lagi.");
        newFileUrl = supabase.storage.from("task-files").getPublicUrl(uploadedPath).data.publicUrl;
      }

      const payload = {
        judul: draft.judul.trim(),
        mata_kuliah: draft.mata_kuliah,
        jenis: draft.jenis,
        deadline: new Date(draft.deadlineDate + "T" + draft.deadlineTime + ":00+07:00").toISOString(),
        ketentuan: draft.ketentuan.trim() || null,
        link_vclass: draft.link_vclass.trim() || null,
        link_pengumpulan: draft.link_pengumpulan.trim() || null,
        file_soal: newFileUrl ?? (draft.removeCurrentFile ? null : task?.file_soal ?? null),
      };

      let saveError: { message: string } | null = null;
      if (task) {
        const result = await supabase.from("tasks").update(payload).eq("id", task.id);
        saveError = result.error;
      } else {
        const result = await supabase.from("tasks").insert(payload);
        saveError = result.error;
      }
      if (saveError) throw new Error(saveError.message);

      const previousPath = storagePathFromUrl(task?.file_soal);
      const currentPath = storagePathFromUrl(payload.file_soal);
      if (previousPath && previousPath !== currentPath) {
        await supabase.storage.from("task-files").remove([previousPath]);
      }

      onSaved();
    } catch (error) {
      if (uploadedPath && supabase) {
        await supabase.storage.from("task-files").remove([uploadedPath]);
      }
      setSubmitError(error instanceof Error ? error.message : "Tugas gagal disimpan. Coba lagi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="admin-form-section" aria-labelledby="task-form-title">
      <div className="admin-section-heading">
        <div>
          <p className="admin-eyebrow">{task ? "UBAH DATA" : "TUGAS BARU"}</p>
          <h2 id="task-form-title">{task ? "Edit tugas" : "Tambah tugas"}</h2>
          <p className="admin-section-description">Kolom bertanda wajib harus diisi. Deadline menggunakan WIB.</p>
        </div>
      </div>

      {submitError && (
        <div className="form-error-summary" role="alert" tabIndex={-1}>
          <strong>Belum bisa disimpan.</strong>
          <p>{submitError}</p>
          {Object.values(errors).length > 0 && (
            <ul>{Object.entries(errors).map(([key, message]) => <li key={key}>{message}</li>)}</ul>
          )}
        </div>
      )}

      <form className="admin-form" onSubmit={handleSubmit} noValidate>
        <div className="form-field">
          <label htmlFor="task-title">Judul tugas <span>Wajib</span></label>
          <input
            ref={titleRef}
            id="task-title"
            name="judul"
            autoComplete="off"
            value={draft.judul}
            maxLength={180}
            onChange={(event) => change("judul", event.target.value)}
            aria-invalid={Boolean(errors.judul)}
            aria-describedby={errors.judul ? "error-judul" : "help-judul"}
          />
          <p className={errors.judul ? "field-hint field-error" : "field-hint"} id={errors.judul ? "error-judul" : "help-judul"}>
            {errors.judul ?? (draft.judul.length + " / 180 karakter")}
          </p>
        </div>

        <div className="form-two-columns">
          <div className="form-field">
            <label htmlFor="task-course">Mata kuliah <span>Wajib</span></label>
            <select
              id="task-course"
              value={draft.mata_kuliah}
              onChange={(event) => change("mata_kuliah", event.target.value)}
              aria-invalid={Boolean(errors.mata_kuliah)}
              aria-describedby={errors.mata_kuliah ? "error-mata-kuliah" : undefined}
            >
              <option value="">Pilih mata kuliah</option>
              {task && !courses.some((course) => course.nama === task.mata_kuliah) && (
                <option value={task.mata_kuliah}>{task.mata_kuliah} (data lama)</option>
              )}
              {courses.map((course) => <option value={course.nama} key={course.id}>{course.nama}</option>)}
            </select>
            {errors.mata_kuliah && <p className="field-hint field-error" id="error-mata-kuliah">{errors.mata_kuliah}</p>}
            {courses.length === 0 && <p className="field-hint">Tambahkan atau aktifkan mata kuliah di katalog terlebih dahulu.</p>}
          </div>
          <div className="form-field">
            <label htmlFor="task-type">Jenis tugas <span>Wajib</span></label>
            <select
              id="task-type"
              value={draft.jenis}
              onChange={(event) => change("jenis", event.target.value)}
              aria-invalid={Boolean(errors.jenis)}
              aria-describedby={errors.jenis ? "error-jenis" : undefined}
            >
              {TASK_TYPES.map((type) => <option value={type} key={type}>{type}</option>)}
            </select>
            {errors.jenis && <p className="field-hint field-error" id="error-jenis">{errors.jenis}</p>}
          </div>
        </div>

        <fieldset className="form-fieldset">
          <legend>Deadline <span>Wajib</span></legend>
          <div className="form-two-columns">
            <div className="form-field">
              <label htmlFor="task-date">Tanggal</label>
              <input
                id="task-date"
                type="date"
                value={draft.deadlineDate}
                onChange={(event) => change("deadlineDate", event.target.value)}
                aria-invalid={Boolean(errors.deadlineDate)}
                aria-describedby={errors.deadlineDate ? "error-deadline-date" : undefined}
              />
              {errors.deadlineDate && <p className="field-hint field-error" id="error-deadline-date">{errors.deadlineDate}</p>}
            </div>
            <div className="form-field">
              <label htmlFor="task-time">Jam (WIB)</label>
              <input
                id="task-time"
                type="time"
                value={draft.deadlineTime}
                onChange={(event) => change("deadlineTime", event.target.value)}
                aria-invalid={Boolean(errors.deadlineTime)}
                aria-describedby={errors.deadlineTime ? "error-deadline-time" : undefined}
              />
              {errors.deadlineTime && <p className="field-hint field-error" id="error-deadline-time">{errors.deadlineTime}</p>}
            </div>
          </div>
        </fieldset>

        <div className="form-field">
          <div className="form-label-row">
            <label htmlFor="task-instructions">Ketentuan & instruksi</label>
            <span className="optional-label">Editor visual + Markdown</span>
          </div>
          <MarkdownEditor
            initialValue={draft.ketentuan}
            onChange={(value) => change("ketentuan", value)}
          />
          <p className="field-hint">Tulis seperti dokumen biasa. Gunakan tombol di atas editor untuk membuat daftar, menebalkan teks, menambah tautan, atau tabel.</p>
        </div>

        <div className="form-two-columns">
          <div className="form-field">
            <label htmlFor="task-vclass">Link VClass <span className="optional-label">Opsional</span></label>
            <input
              id="task-vclass"
              type="url"
              inputMode="url"
              autoComplete="url"
              value={draft.link_vclass}
              onChange={(event) => change("link_vclass", event.target.value)}
              placeholder="https://vclass.unila.ac.id/…"
              aria-invalid={Boolean(errors.link_vclass)}
              aria-describedby={errors.link_vclass ? "error-vclass" : undefined}
            />
            {errors.link_vclass && <p className="field-hint field-error" id="error-vclass">{errors.link_vclass}</p>}
          </div>
          <div className="form-field">
            <label htmlFor="task-submission">Link pengumpulan <span className="optional-label">Opsional</span></label>
            <input
              id="task-submission"
              type="url"
              inputMode="url"
              autoComplete="url"
              value={draft.link_pengumpulan}
              onChange={(event) => change("link_pengumpulan", event.target.value)}
              placeholder="https://…"
              aria-invalid={Boolean(errors.link_pengumpulan)}
              aria-describedby={errors.link_pengumpulan ? "error-submission" : undefined}
            />
            {errors.link_pengumpulan && <p className="field-hint field-error" id="error-submission">{errors.link_pengumpulan}</p>}
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="task-file">Lampiran <span className="optional-label">Opsional · maksimal 10 MB</span></label>
          {task?.file_soal && (
            <div className="current-file">
              <a href={task.file_soal} target="_blank" rel="noreferrer">Buka lampiran saat ini ↗</a>
              <label className="remove-file-control">
                <input
                  type="checkbox"
                  checked={draft.removeCurrentFile}
                  onChange={(event) => change("removeCurrentFile", event.target.checked)}
                  disabled={Boolean(draft.file)}
                />
                Hapus lampiran saat ini
              </label>
            </div>
          )}
          <input
            id="task-file"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.docx,.zip"
            onChange={(event) => {
              change("file", event.target.files?.[0] ?? null);
            }}
            aria-invalid={Boolean(errors.file)}
            aria-describedby={errors.file ? "error-file" : "help-file"}
          />
          <p className={errors.file ? "field-hint field-error" : "field-hint"} id={errors.file ? "error-file" : "help-file"}>
            {errors.file ?? "Format: PDF, PNG, JPG, DOCX, ZIP."}
          </p>
        </div>

        <div className="form-actions">
          <button className="primary-action" type="submit" disabled={saving || (courses.length === 0 && !task)}>
            {saving ? "Menyimpan…" : task ? "Simpan perubahan" : "Simpan tugas"}
          </button>
          <button className="quiet-button" type="button" onClick={onCancel} disabled={saving}>Batal</button>
        </div>
      </form>
    </section>
  );
}

function AdminLogin({
  onAuthenticated,
}: {
  onAuthenticated: () => void;
}) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setNotice("");
    const normalizedEmail = email.trim().toLowerCase();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setErrorMessage("Masukkan alamat email yang valid.");
      return;
    }
    if (password.length < 6) {
      setErrorMessage("Kata sandi minimal 6 karakter.");
      return;
    }
    if (mode === "signup" && password !== confirmPassword) {
      setErrorMessage("Konfirmasi kata sandi belum cocok.");
      return;
    }
    if (!supabase) {
      setErrorMessage("Supabase belum dikonfigurasi.");
      return;
    }

    setBusy(true);
    try {
      const allowlist = await checkAdminAllowlist(normalizedEmail);
      if (allowlist.error) {
        setErrorMessage(allowlist.error);
        return;
      }
      if (!allowlist.allowed) {
        setErrorMessage("Email ini belum terdaftar sebagai admin. Minta Super Admin menambahkannya terlebih dahulu.");
        return;
      }

      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword({
          email: normalizedEmail,
          password,
        });
        if (error) {
          setErrorMessage("Login gagal. Periksa kembali email dan kata sandi.");
          return;
        }
        onAuthenticated();
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: normalizedEmail,
          password,
        });
        if (error) {
          setErrorMessage(error.message);
          return;
        }
        if (data.session) {
          setNotice("Akun berhasil dibuat. Memeriksa akses admin…");
          onAuthenticated();
        } else {
          setNotice("Pendaftaran dikirim. Periksa email untuk konfirmasi, lalu masuk menggunakan kata sandi tadi.");
          setMode("login");
          setPassword("");
          setConfirmPassword("");
        }
      }
    } catch {
      setErrorMessage("Permintaan belum berhasil. Periksa koneksi internet dan coba lagi.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-section">
      <p className="admin-eyebrow">AKSES TERBATAS</p>
      <h1>Panel admin</h1>
      <p className="admin-section-description">
        Masuk menggunakan akun yang emailnya sudah terdaftar dalam daftar admin.
      </p>

      <div className="auth-tabs" role="group" aria-label="Jenis autentikasi">
        <button className={mode === "login" ? "auth-tab is-current" : "auth-tab"} type="button" onClick={() => { setMode("login"); setErrorMessage(""); setNotice(""); }}>
          Masuk
        </button>
        <button className={mode === "signup" ? "auth-tab is-current" : "auth-tab"} type="button" onClick={() => { setMode("signup"); setErrorMessage(""); setNotice(""); }}>
          Daftar akun
        </button>
      </div>

      {errorMessage && <div className="form-error-summary" role="alert"><strong>Belum bisa melanjutkan.</strong><p>{errorMessage}</p></div>}
      {notice && <p className="form-success-note" role="status">{notice}</p>}

      <form className="admin-form auth-form" onSubmit={submit} noValidate>
        <div className="form-field">
          <label htmlFor="admin-email">Email</label>
          <input id="admin-email" type="email" autoComplete="email" inputMode="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>
        <div className="form-field">
          <label htmlFor="admin-password">Kata sandi</label>
          <input id="admin-password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} minLength={6} required />
          <p className="field-hint">Minimal 6 karakter.</p>
        </div>
        {mode === "signup" && (
          <div className="form-field">
            <label htmlFor="admin-confirm-password">Ulangi kata sandi</label>
            <input id="admin-confirm-password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={6} required />
          </div>
        )}
        <button className="primary-action" type="submit" disabled={busy}>
          {busy ? "Memeriksa…" : mode === "login" ? "Masuk ke panel" : "Daftar akun admin"}
        </button>
      </form>
      <p className="auth-footnote">Akses tulis tetap dibatasi oleh policy Row Level Security di Supabase.</p>
    </section>
  );
}

export default function AdminPanel({ tasks, courses, onBack, onDataChanged }: AdminPanelProps) {
  const [sessionEmail, setSessionEmail] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [access, setAccess] = useState<AccessState>("none");
  const [accessMessage, setAccessMessage] = useState("");
  const [search, setSearch] = useState("");
  const [formTask, setFormTask] = useState<Task | null | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    if (!supabase) {
      setAuthReady(true);
      return;
    }
    let alive = true;
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSessionEmail(session?.user.email?.trim().toLowerCase() ?? null);
      setAuthReady(true);
    });
    void supabase.auth.getSession().then(({ data, error }) => {
      if (!alive) return;
      setSessionEmail(error ? null : data.session?.user.email?.trim().toLowerCase() ?? null);
      setAuthReady(true);
    });
    return () => {
      alive = false;
      subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    let alive = true;
    if (!supabase || !sessionEmail) {
      setAccess("none");
      setAccessMessage("");
      return;
    }
    setAccess("checking");
    void checkAdminAllowlist(sessionEmail).then((result) => {
      if (!alive) return;
      setAccessMessage(result.error ?? "");
      setAccess(result.error ? "error" : result.allowed ? "allowed" : "denied");
    });
    return () => {
      alive = false;
    };
  }, [sessionEmail]);

  const filteredTasks = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase("id-ID");
    return [...tasks]
      .filter((task) => !keyword || [task.judul, task.mata_kuliah, task.jenis].some((value) => value.toLocaleLowerCase("id-ID").includes(keyword)))
      .sort((a, b) => a.deadline.localeCompare(b.deadline));
  }, [tasks, search]);

  async function signOut() {
    if (!supabase) return;
    await supabase.auth.signOut();
    setFormTask(undefined);
  }

  async function removeTask() {
    if (!supabase || !deleteTarget) return;
    setDeleting(true);
    setDeleteError("");
    const target = deleteTarget;
    const { error } = await supabase.from("tasks").delete().eq("id", target.id);
    if (error) {
      setDeleteError("Tugas belum terhapus. Periksa akses admin lalu coba lagi.");
      setDeleting(false);
      return;
    }
    const path = storagePathFromUrl(target.file_soal);
    if (path) await supabase.storage.from("task-files").remove([path]);
    setDeleteTarget(null);
    setDeleting(false);
    onDataChanged();
  }

  return (
    <main className="app-shell admin-shell">
      <header className="app-header">
        <a className="wordmark" href="/" onClick={(event) => { event.preventDefault(); onBack(); }} aria-label="Kembali ke agenda">
          <span className="wordmark-symbol" aria-hidden="true">t<span>.</span></span>
          <span className="wordmark-name">tugas kuliah</span>
        </a>
        <div className="admin-header-actions">
          {sessionEmail && <span className="admin-email">{sessionEmail}</span>}
          {sessionEmail && <button className="quiet-button" type="button" onClick={() => void signOut()}>Keluar</button>}
          <button className="quiet-button" type="button" onClick={onBack}>Agenda</button>
        </div>
      </header>

      {!authReady ? (
        <section className="auth-section" role="status"><span className="loading-mark" /><p>Memeriksa sesi…</p></section>
      ) : supabaseConfigMissing ? (
        <section className="auth-section"><div className="form-error-summary" role="alert"><strong>Supabase belum dikonfigurasi.</strong><p>Lengkapi VITE_SUPABASE_URL dan VITE_SUPABASE_ANON_KEY di file .env.local.</p></div></section>
      ) : !sessionEmail ? (
        <AdminLogin onAuthenticated={() => setAccess("checking")} />
      ) : access === "checking" ? (
        <section className="auth-section" role="status"><span className="loading-mark" /><p>Memeriksa izin admin…</p></section>
      ) : access === "error" ? (
        <section className="auth-section">
          <div className="form-error-summary" role="alert"><strong>Izin admin tidak bisa diverifikasi.</strong><p>{accessMessage}</p></div>
          <button className="quiet-button" type="button" onClick={() => void signOut()}>Keluar</button>
        </section>
      ) : access === "denied" ? (
        <section className="auth-section">
          <div className="form-error-summary" role="alert"><strong>Akun ini bukan admin.</strong><p>Email {sessionEmail} tidak terdaftar pada tabel admin_users. Hubungi Super Admin untuk meminta akses.</p></div>
          <button className="quiet-button" type="button" onClick={() => void signOut()}>Keluar dari akun ini</button>
        </section>
      ) : (
        <section className="admin-workspace">
          {formTask !== undefined ? (
            <div className="task-editor-page">
              <button className="back-to-list" type="button" onClick={() => setFormTask(undefined)}>
                <span aria-hidden="true">←</span> Kembali ke daftar tugas
              </button>
              <TaskForm
                key={formTask ? formTask.id : "new-task"}
                task={formTask}
                courses={courses}
                onCancel={() => setFormTask(undefined)}
                onSaved={() => {
                  setFormTask(undefined);
                  onDataChanged();
                }}
              />
            </div>
          ) : (
            <>
              <div className="admin-welcome">
                <div>
                  <p className="admin-eyebrow">PENGELOLAAN AKADEMIK</p>
                  <h1>Kelola tugas</h1>
                  <p className="admin-section-description">
                    Pilih tugas untuk mengubah detailnya, atau hapus jika sudah tidak diperlukan.
                  </p>
                </div>
                <button
                  className="primary-action add-task-button"
                  type="button"
                  onClick={() => setFormTask(null)}
                  disabled={courses.length === 0}
                >
                  <span aria-hidden="true">＋</span> Tambah tugas
                </button>
              </div>

              {courses.length === 0 && (
                <p className="admin-inline-note">
                  Belum ada mata kuliah aktif. Tambahkan atau aktifkan mata kuliah sebelum membuat tugas.
                </p>
              )}

              <section className="admin-task-list-section" aria-labelledby="admin-task-list-title">
                <div className="admin-section-heading">
                  <div>
                    <h2 id="admin-task-list-title">Daftar tugas</h2>
                    <p className="admin-section-description">
                      {filteredTasks.length} tugas. Tombol Edit untuk mengubah detail; Hapus untuk menghapus permanen.
                    </p>
                  </div>
                  <label className="admin-search">
                    <span aria-hidden="true">⌕</span>
                    <input
                      type="search"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Cari judul atau mata kuliah…"
                      aria-label="Cari tugas di panel admin"
                    />
                  </label>
                </div>

                {filteredTasks.length === 0 ? (
                  <p className="admin-inline-note">
                    {tasks.length === 0
                      ? "Belum ada tugas. Tekan Tambah tugas untuk membuat yang pertama."
                      : "Tidak ada tugas yang cocok dengan pencarian."}
                  </p>
                ) : (
                  <div className="managed-task-list">
                    {filteredTasks.map((task) => (
                      <article className="managed-task-row" key={task.id}>
                        <div className="managed-task-copy">
                          <span className="managed-task-course">
                            {task.mata_kuliah} <span aria-hidden="true">·</span> {task.jenis}
                          </span>
                          <h3>{task.judul}</h3>
                          <p>
                            Deadline: {new Intl.DateTimeFormat("id-ID", {
                              dateStyle: "medium",
                              timeStyle: "short",
                              timeZone: "Asia/Jakarta",
                            }).format(new Date(task.deadline))} WIB
                          </p>
                        </div>
                        <div className="managed-task-actions">
                          <button
                            className="edit-task-button"
                            type="button"
                            onClick={() => setFormTask(task)}
                            aria-label={"Edit tugas " + task.judul}
                          >
                            <span aria-hidden="true">✎</span> Edit tugas
                          </button>
                          <button
                            className="delete-task-button"
                            type="button"
                            onClick={() => { setDeleteTarget(task); setDeleteError(""); }}
                            aria-label={"Hapus tugas " + task.judul}
                          >
                            <span aria-hidden="true">×</span> Hapus
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              {deleteTarget && (
                <div className="delete-dialog-backdrop">
                  <section
                    className="delete-dialog"
                    role="alertdialog"
                    aria-modal="true"
                    aria-labelledby="delete-title"
                    aria-describedby="delete-description"
                  >
                    <p className="admin-eyebrow">KONFIRMASI PENGHAPUSAN</p>
                    <h2 id="delete-title">Hapus tugas ini?</h2>
                    <p id="delete-description">
                      <strong>{deleteTarget.judul}</strong> akan dihapus permanen dari daftar tugas.
                      Tindakan ini tidak bisa dibatalkan.
                    </p>
                    {deleteError && <p className="delete-dialog-error" role="alert">{deleteError}</p>}
                    <div className="delete-dialog-actions">
                      <button
                        className="danger-action"
                        type="button"
                        onClick={() => void removeTask()}
                        disabled={deleting}
                      >
                        {deleting ? "Menghapus…" : "Ya, hapus tugas"}
                      </button>
                      <button
                        className="quiet-button"
                        type="button"
                        onClick={() => { setDeleteTarget(null); setDeleteError(""); }}
                        disabled={deleting}
                      >
                        Batal
                      </button>
                    </div>
                  </section>
                </div>
              )}
            </>
          )}
        </section>
      )}
    </main>
  );
}
