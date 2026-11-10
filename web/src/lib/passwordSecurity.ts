const PASSWORD_SYMBOLS = "!@#$%^&*()_+-=[]{};'\\:\"|<>?,./`~";

export const PASSWORD_MIN_LENGTH = 12;

/**
 * Front-end password policy for the admin signup form.
 * Supabase Auth remains the authoritative authentication service.
 */
export function getPasswordPolicyError(password: string): string | null {
  if ([...password].length < PASSWORD_MIN_LENGTH) {
    return `Kata sandi minimal ${PASSWORD_MIN_LENGTH} karakter.`;
  }
  if (!/[a-z]/.test(password)) {
    return "Tambahkan setidaknya satu huruf kecil (a-z).";
  }
  if (!/[A-Z]/.test(password)) {
    return "Tambahkan setidaknya satu huruf besar (A-Z).";
  }
  if (!/[0-9]/.test(password)) {
    return "Tambahkan setidaknya satu angka (0-9).";
  }
  if (![...PASSWORD_SYMBOLS].some((symbol) => password.includes(symbol))) {
    return "Tambahkan setidaknya satu simbol, misalnya ! atau #.";
  }
  return null;
}

/**
 * Checks the password against HIBP Pwned Passwords using k-anonymity.
 * The raw password and complete SHA-1 digest never leave this browser.
 */
export async function checkPwnedPassword(password: string): Promise<boolean> {
  if (!globalThis.crypto?.subtle) {
    throw new Error("Browser tidak mendukung pemeriksaan kata sandi aman. Perbarui browser lalu coba lagi.");
  }

  try {
    const digest = await globalThis.crypto.subtle.digest(
      "SHA-1",
      new TextEncoder().encode(password),
    );
    const hash = Array.from(new Uint8Array(digest), (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("").toUpperCase();

    const prefix = hash.slice(0, 5);
    const suffix = hash.slice(5);
    const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`, {
      method: "GET",
      headers: { "Add-Padding": "true" },
      cache: "no-store",
      credentials: "omit",
      referrerPolicy: "no-referrer",
    });

    if (!response.ok) {
      throw new Error("Pemeriksaan kata sandi bocor sedang tidak tersedia. Coba lagi nanti.");
    }

    const lines = (await response.text()).split(/\\r?\\n/);
    const match = lines.find((line) => {
      const separator = line.indexOf(":");
      return separator > 0 && line.slice(0, separator).trim().toUpperCase() === suffix;
    });
    if (!match) return false;

    const count = Number(match.slice(match.indexOf(":") + 1).trim());
    return Number.isFinite(count) && count > 0;
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("Pemeriksaan kata sandi bocor")) {
      throw error;
    }
    throw new Error("Pemeriksaan kata sandi bocor gagal. Periksa koneksi internet lalu coba lagi.");
  }
}
