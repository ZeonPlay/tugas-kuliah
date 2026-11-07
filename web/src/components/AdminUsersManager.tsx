import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { supabase } from "../lib/supabase";

type Props = {
  currentEmail: string;
  superAdminEmail: string;
};

type AdminUser = { email: string };

export default function AdminUsersManager({ currentEmail, superAdminEmail }: Props) {
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [pendingRemoval, setPendingRemoval] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [notice, setNotice] = useState("");

  const normalizedSuperAdmin = superAdminEmail.trim().toLowerCase();
  const isSuperAdmin = Boolean(normalizedSuperAdmin) &&
    currentEmail.trim().toLowerCase() === normalizedSuperAdmin;

  async function loadAdmins() {
    if (!supabase || !isSuperAdmin) {
      setLoading(false);
      return;
    }

    setLoading(true);
    const { data, error } = await supabase
      .from("admin_users")
      .select("email")
      .order("email", { ascending: true });

    if (error) {
      setErrorMessage("Daftar admin gagal dimuat. Periksa izin baca tabel admin_users: " + error.message);
      setAdmins([]);
    } else {
      setErrorMessage("");
      setAdmins((data ?? []).map((item) => ({ email: String(item.email ?? "").trim().toLowerCase() })).filter((item) => item.email));
    }
    setLoading(false);
  }

  useEffect(() => {
    void loadAdmins();
    // loadAdmins uses the current authenticated session and role from props.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentEmail, superAdminEmail]);

  async function addAdmin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase || !isSuperAdmin || saving) return;

    const normalizedEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setErrorMessage("Masukkan alamat email yang valid.");
      setNotice("");
      return;
    }
    if (admins.some((admin) => admin.email === normalizedEmail)) {
      setErrorMessage("Email tersebut sudah terdaftar sebagai admin.");
      setNotice("");
      return;
    }

    setSaving(true);
    setErrorMessage("");
    setNotice("");
    const { error } = await supabase.from("admin_users").insert({ email: normalizedEmail });

    if (error) {
      setErrorMessage("Email admin belum berhasil ditambahkan: " + error.message);
      setSaving(false);
      return;
    }

    setEmail("");
    setNotice("Akses admin ditambahkan untuk " + normalizedEmail + ". Pengguna tersebut dapat membuat akun lewat tab Daftar Akun.");
    await loadAdmins();
    setSaving(false);
  }

  async function removeAdmin(targetEmail: string) {
    if (!supabase || !isSuperAdmin || targetEmail === normalizedSuperAdmin || removing) return;

    setRemoving(targetEmail);
    setErrorMessage("");
    setNotice("");
    const { error } = await supabase.from("admin_users").delete().eq("email", targetEmail);

    if (error) {
      setErrorMessage("Akses admin belum berhasil dicabut: " + error.message);
      setRemoving(null);
      setPendingRemoval(null);
      return;
    }

    setNotice("Akses admin untuk " + targetEmail + " berhasil dicabut.");
    setRemoving(null);
    setPendingRemoval(null);
    await loadAdmins();
  }

  if (!isSuperAdmin) {
    return (
      <section className="admin-users-section">
        <div className="form-error-summary" role="alert">
          <strong>Akses Super Admin diperlukan.</strong>
          <p>Bagian ini hanya dapat digunakan oleh email yang diatur pada VITE_ADMIN_EMAIL.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="admin-users-section" aria-labelledby="admin-users-title">
      <div className="admin-section-heading">
        <div>
          <p className="admin-eyebrow">AKSES & PERIZINAN</p>
          <h1 id="admin-users-title">Kelola admin</h1>
          <p className="admin-section-description">
            Tambahkan email ke daftar izin atau cabut akses pengelolaan tugas, mata kuliah, dan arsip modul.
          </p>
        </div>
        <span className="admin-users-count">{loading ? "…" : admins.length} admin</span>
      </div>

      <form className="admin-users-add-form" onSubmit={addAdmin}>
        <div className="admin-users-add-copy">
          <label htmlFor="new-admin-email">Email admin baru</label>
          <p>Pengguna harus mendaftar akun melalui tab Daftar Akun setelah emailnya diizinkan di sini.</p>
        </div>
        <div className="admin-users-add-controls">
          <input
            id="new-admin-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nama@email.com"
            required
            disabled={saving}
          />
          <button className="primary-action" type="submit" disabled={saving}>
            {saving ? "Menambahkan…" : "＋ Tambah admin"}
          </button>
        </div>
      </form>

      {errorMessage && <p className="admin-users-feedback is-error" role="alert">{errorMessage}</p>}
      {notice && <p className="admin-users-feedback is-success" role="status">{notice}</p>}

      <div className="admin-users-list-heading">
        <h2>Daftar email yang diizinkan</h2>
        <button className="group-tool-button" type="button" onClick={() => void loadAdmins()} disabled={loading}>
          Muat ulang
        </button>
      </div>

      {loading ? (
        <div className="admin-users-empty" role="status"><span className="loading-mark" />Memuat daftar admin…</div>
      ) : admins.length === 0 ? (
        <div className="admin-users-empty">Belum ada email yang terdaftar pada tabel admin_users.</div>
      ) : (
        <ul className="admin-users-list">
          {admins.map((admin) => {
            const isProtected = admin.email === normalizedSuperAdmin;
            return (
              <li className="admin-users-row" key={admin.email}>
                <span className="admin-users-avatar" aria-hidden="true">{admin.email.charAt(0).toUpperCase()}</span>
                <span className="admin-users-email">
                  <strong>{admin.email}</strong>
                  <small>{isProtected ? "Super Admin · akses utama dilindungi" : "Admin"}</small>
                </span>
                {isProtected ? (
                  <span className="admin-users-protected">Dilindungi</span>
                ) : pendingRemoval === admin.email ? (
                  <span className="admin-users-confirm">
                    <span>Cabut akses?</span>
                    <button type="button" className="admin-users-confirm-delete" disabled={removing !== null} onClick={() => void removeAdmin(admin.email)}>
                      {removing === admin.email ? "Mencabut…" : "Ya, cabut"}
                    </button>
                    <button type="button" className="group-tool-button" disabled={removing !== null} onClick={() => setPendingRemoval(null)}>Batal</button>
                  </span>
                ) : (
                  <button type="button" className="admin-users-remove" onClick={() => { setPendingRemoval(admin.email); setNotice(""); setErrorMessage(""); }}>
                    Cabut akses
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <p className="admin-users-security-note">
        Catatan: pengaturan ini mengubah daftar izin admin di Supabase. Perubahan akses database tetap mengikuti kebijakan RLS project.
      </p>
    </section>
  );
}
