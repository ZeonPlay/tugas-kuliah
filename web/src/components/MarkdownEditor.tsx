import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "@tiptap/markdown";
import Placeholder from "@tiptap/extension-placeholder";
import { Table } from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import MarkdownContent, { normalizeLegacyMarkdown } from "./MarkdownContent";

type MarkdownEditorProps = {
  initialValue: string;
  onChange: (value: string) => void;
};

type EditorView = "write" | "preview";
type SavedRange = { from: number; to: number };

function EditorTool({
  children,
  label,
  active = false,
  disabled = false,
  danger = false,
  onClick,
}: {
  children: ReactNode;
  label: string;
  active?: boolean;
  disabled?: boolean;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={"tiptap-tool" + (active ? " is-active" : "") + (danger ? " is-danger" : "")}
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

/**
 * Document-style WYSIWYG editor. Keep Markdown as the persisted format so
 * existing Supabase rows and the legacy Streamlit app remain compatible.
 * Preview uses the very same renderer as the student-facing task description.
 */
export default function MarkdownEditor({ initialValue, onChange }: MarkdownEditorProps) {
  const onChangeRef = useRef(onChange);
  const lastPropValueRef = useRef(initialValue);
  const lastEmittedValueRef = useRef<string | null>(null);
  const linkSelectionRef = useRef<SavedRange | null>(null);

  const [markdown, setMarkdown] = useState(() => normalizeLegacyMarkdown(initialValue));
  const [view, setView] = useState<EditorView>("write");
  const [linkPanelOpen, setLinkPanelOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkText, setLinkText] = useState("");
  const [linkError, setLinkError] = useState("");
  const [selectionInTable, setSelectionInTable] = useState(false);
  const [tableNotice, setTableNotice] = useState("");

  onChangeRef.current = onChange;

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        link: {
          openOnClick: false,
          autolink: false,
          linkOnPaste: false,
        },
      }),
      Table.configure({ resizable: true, allowTableNodeSelection: true }),
      TableRow,
      TableHeader,
      TableCell,
      Markdown.configure({
        markedOptions: { gfm: true },
      }),
      Placeholder.configure({
        placeholder: "Mulai menulis instruksi tugas…",
      }),
    ],
    content: initialValue,
    contentType: "markdown",
    editorProps: {
      attributes: {
        class: "tiptap-editor-content",
        "aria-label": "Ketentuan dan instruksi tugas",
        spellcheck: "true",
      },
    },
    onUpdate: ({ editor: currentEditor }) => {
      const nextMarkdown = currentEditor.getMarkdown();
      lastEmittedValueRef.current = nextMarkdown;
      setMarkdown(nextMarkdown);
      onChangeRef.current(nextMarkdown);
      setLinkError("");
      setSelectionInTable(currentEditor.isActive("table"));
      setTableNotice("");
    },
    onSelectionUpdate: ({ editor: currentEditor }) => {
      setSelectionInTable(currentEditor.isActive("table"));
    },
  });

  // Sync a genuinely new document into the editor without resetting the
  // cursor whenever the parent receives the Markdown emitted while typing.
  useEffect(() => {
    if (!editor || initialValue === lastPropValueRef.current) return;
    lastPropValueRef.current = initialValue;

    if (lastEmittedValueRef.current === initialValue) {
      lastEmittedValueRef.current = null;
      setMarkdown(initialValue);
      return;
    }

    lastEmittedValueRef.current = null;
    editor.commands.setContent(initialValue, { contentType: "markdown", emitUpdate: false });
    setMarkdown(normalizeLegacyMarkdown(initialValue));
    setView("write");
    setLinkPanelOpen(false);
    setLinkError("");
  }, [editor, initialValue]);

  function insertTable() {
    if (!editor) return;
    setTableNotice("");
    if (editor.isActive("table")) {
      setTableNotice("Kursor sedang berada di tabel. Gunakan tombol tambah baris/kolom, atau pindahkan kursor ke luar tabel untuk membuat tabel baru.");
      return;
    }

    editor.chain().focus().insertTable({ rows: 3, cols: 2, withHeaderRow: true }).run();
    setTableNotice("Tabel ditambahkan. Klik sel untuk mengetik; gunakan Tab untuk berpindah antarsel.");
  }

  function openLinkPanel() {
    if (!editor) return;

    // Selecting an existing link first makes editing its URL easier on both
    // desktop and touch screens.
    if (editor.isActive("link") && editor.state.selection.empty) {
      editor.chain().extendMarkRange("link").run();
    }

    const selection = editor.state.selection;
    const range = { from: selection.from, to: selection.to };
    linkSelectionRef.current = range;
    setLinkUrl((editor.getAttributes("link").href as string | undefined) ?? "");
    setLinkText(editor.state.doc.textBetween(range.from, range.to, " "));
    setLinkError("");
    setLinkPanelOpen((open) => !open);
  }

  function saveLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor) return;

    const range = linkSelectionRef.current;
    if (!range) {
      setLinkError("Pilih posisi teks terlebih dahulu.");
      return;
    }

    const href = linkUrl.trim();
    if (href) {
      try {
        const parsed = new URL(href);
        if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
          setLinkError("Tautan harus menggunakan http:// atau https://.");
          return;
        }
      } catch {
        setLinkError("Masukkan URL lengkap yang diawali https:// atau http://.");
        return;
      }
    }

    const chain = editor.chain().focus().setTextSelection(range);
    if (!href) {
      if (range.from === range.to) {
        editor.chain().focus().extendMarkRange("link").unsetLink().run();
      } else {
        chain.unsetLink().run();
      }
      setLinkPanelOpen(false);
      return;
    }

    if (range.from !== range.to) {
      chain.setLink({ href }).run();
    } else {
      const label = linkText.trim();
      if (!label) {
        setLinkError("Isi teks tautan jika belum memilih teks di dokumen.");
        return;
      }
      chain
        .insertContent({
          type: "text",
          text: label,
          marks: [{ type: "link", attrs: { href } }],
        })
        .run();
    }

    setLinkPanelOpen(false);
    setLinkError("");
  }

  const blockStyle = editor
    ? editor.isActive("heading", { level: 1 })
      ? "h1"
      : editor.isActive("heading", { level: 2 })
        ? "h2"
        : editor.isActive("heading", { level: 3 })
          ? "h3"
          : "paragraph"
    : "paragraph";
  const wordCount = markdown.trim() ? markdown.trim().split(/\s+/).filter(Boolean).length : 0;

  return (
    <div className="tiptap-editor-shell">
      <div className="tiptap-editor-header">
        <div className="tiptap-editor-identity">
          <span className="tiptap-document-mark" aria-hidden="true">¶</span>
          <div>
            <span className="tiptap-editor-title">Dokumen instruksi</span>
            <span className="tiptap-editor-subtitle">Pemformatan yang kompatibel dengan Markdown</span>
          </div>
        </div>
        <div className="tiptap-view-switch" role="group" aria-label="Tampilan editor">
          <button
            type="button"
            className={view === "write" ? "is-active" : ""}
            aria-pressed={view === "write"}
            onClick={() => setView("write")}
          >
            <span aria-hidden="true">✎</span> Tulis
          </button>
          <button
            type="button"
            className={view === "preview" ? "is-active" : ""}
            aria-pressed={view === "preview"}
            onClick={() => setView("preview")}
          >
            <span aria-hidden="true">◉</span> Pratinjau
          </button>
        </div>
      </div>

      {!editor ? (
        <div className="tiptap-toolbar-loading">Menyiapkan editor…</div>
      ) : view === "write" ? (
        <>
          <div className="tiptap-toolbar" role="toolbar" aria-label="Pemformatan instruksi">
            <div className="tiptap-tool-group tiptap-style-group" role="group" aria-label="Gaya teks">
              <select
                className="tiptap-format-select"
                aria-label="Gaya paragraf"
                value={blockStyle}
                onChange={(event) => {
                  if (event.target.value === "paragraph") {
                    editor.chain().focus().setParagraph().run();
                  } else {
                    const level = Number(event.target.value.slice(1)) as 1 | 2 | 3;
                    editor.chain().focus().toggleHeading({ level }).run();
                  }
                }}
              >
                <option value="paragraph">Paragraf</option>
                <option value="h1">Judul 1</option>
                <option value="h2">Judul 2</option>
                <option value="h3">Judul 3</option>
              </select>
            </div>

            <span className="tiptap-toolbar-divider" aria-hidden="true" />

            <div className="tiptap-tool-group" role="group" aria-label="Format karakter">
              <EditorTool label="Tebal (Ctrl+B)" active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}>
                <strong>B</strong>
              </EditorTool>
              <EditorTool label="Miring (Ctrl+I)" active={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()}>
                <em>I</em>
              </EditorTool>
              <EditorTool label="Coret" active={editor.isActive("strike")} onClick={() => editor.chain().focus().toggleStrike().run()}>
                <s>S</s>
              </EditorTool>
              <EditorTool label="Kode sebaris" active={editor.isActive("code")} onClick={() => editor.chain().focus().toggleCode().run()}>
                <code>{"</>"}</code>
              </EditorTool>
            </div>

            <span className="tiptap-toolbar-divider" aria-hidden="true" />

            <div className="tiptap-tool-group" role="group" aria-label="Daftar dan kutipan">
              <EditorTool label="Daftar bullet" active={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()}>
                <span aria-hidden="true">•</span> Daftar
              </EditorTool>
              <EditorTool label="Daftar bernomor" active={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()}>
                <span aria-hidden="true">1.</span> Bernomor
              </EditorTool>
              <EditorTool label="Kutipan" active={editor.isActive("blockquote")} onClick={() => editor.chain().focus().toggleBlockquote().run()}>
                “ Kutipan
              </EditorTool>
              <EditorTool label="Blok kode" active={editor.isActive("codeBlock")} onClick={() => editor.chain().focus().toggleCodeBlock().run()}>
                {"</> Blok"}
              </EditorTool>
            </div>

            <span className="tiptap-toolbar-divider" aria-hidden="true" />

            <div className="tiptap-tool-group" role="group" aria-label="Sisipkan konten">
              <EditorTool label="Sisipkan tautan" active={editor.isActive("link") || linkPanelOpen} onClick={openLinkPanel}>
                ↗ Tautan
              </EditorTool>
              {selectionInTable ? (
                <>
                  <EditorTool label="Tambah baris di bawah" onClick={() => editor.chain().focus().addRowAfter().run()}>
                    + Baris
                  </EditorTool>
                  <EditorTool label="Tambah kolom di kanan" onClick={() => editor.chain().focus().addColumnAfter().run()}>
                    + Kolom
                  </EditorTool>
                  <EditorTool label="Hapus baris saat ini" danger onClick={() => editor.chain().focus().deleteRow().run()}>
                    − Baris
                  </EditorTool>
                  <EditorTool label="Hapus kolom saat ini" danger onClick={() => editor.chain().focus().deleteColumn().run()}>
                    − Kolom
                  </EditorTool>
                  <EditorTool
                    label="Hapus seluruh tabel"
                    danger
                    onClick={() => {
                      if (window.confirm("Hapus seluruh tabel ini? Perubahan bisa dibatalkan sebelum tugas disimpan.")) {
                        editor.chain().focus().deleteTable().run();
                        setTableNotice("Tabel dihapus dari instruksi. Perubahan belum disimpan.");
                      }
                    }}
                  >
                    × Tabel
                  </EditorTool>
                </>
              ) : (
                <EditorTool label="Tambahkan tabel dengan tiga baris dan dua kolom" onClick={insertTable}>
                  ▦ Tabel
                </EditorTool>
              )}
              <EditorTool label="Garis pemisah" onClick={() => editor.chain().focus().setHorizontalRule().run()}>
                — Garis
              </EditorTool>
            </div>

            <span className="tiptap-toolbar-divider" aria-hidden="true" />

            <div className="tiptap-tool-group tiptap-history-group" role="group" aria-label="Riwayat">
              <EditorTool label="Urungkan" disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()}>
                ↶
              </EditorTool>
              <EditorTool label="Ulangi" disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()}>
                ↷
              </EditorTool>
            </div>
          </div>

          {linkPanelOpen && (
            <form className="tiptap-link-panel" onSubmit={saveLink}>
              <div className="tiptap-link-fields">
                <label>
                  Alamat tautan
                  <input
                    type="url"
                    inputMode="url"
                    autoComplete="url"
                    placeholder="https://contoh.com"
                    value={linkUrl}
                    onChange={(event) => setLinkUrl(event.target.value)}
                    aria-invalid={Boolean(linkError)}
                  />
                </label>
                {linkSelectionRef.current?.from === linkSelectionRef.current?.to && (
                  <label>
                    Teks yang ditampilkan
                    <input
                      type="text"
                      placeholder="Buka materi"
                      value={linkText}
                      onChange={(event) => setLinkText(event.target.value)}
                    />
                  </label>
                )}
              </div>
              {linkError && <p className="tiptap-link-error-message" role="alert">{linkError}</p>}
              <div className="tiptap-link-actions">
                <button type="button" className="tiptap-secondary-action" onClick={() => setLinkPanelOpen(false)}>Batal</button>
                <button type="submit" className="tiptap-primary-action">Terapkan tautan</button>
              </div>
              <p className="tiptap-link-note">URL harus memakai http:// atau https://. Kosongkan URL untuk menghapus tautan dari teks terpilih.</p>
            </form>
          )}

          {selectionInTable && (
            <p className="tiptap-status-note" role="status">
              Kursor ada di tabel. Tombol baris dan kolom muncul di toolbar; gunakan Tab untuk berpindah antarsel.
            </p>
          )}
          {tableNotice && <p className="tiptap-status-note" role="status">{tableNotice}</p>}

          <div className="tiptap-workspace">
            <div className="tiptap-page">
              <EditorContent editor={editor} />
            </div>
          </div>
        </>
      ) : (
        <div className="tiptap-preview-workspace">
          <div className="tiptap-preview-page">
            <div className="tiptap-preview-label">
              <span>PRATINJAU MAHASISWA</span>
              <span>Render Markdown yang sama dengan halaman utama</span>
            </div>
            {normalizeLegacyMarkdown(markdown) ? (
              <MarkdownContent content={markdown} className="tiptap-preview-content" />
            ) : (
              <p className="tiptap-preview-empty">Belum ada instruksi. Kembali ke tab Tulis untuk mulai membuatnya.</p>
            )}
          </div>
        </div>
      )}

      <div className="tiptap-editor-footer">
        <span><span className="tiptap-footer-dot" aria-hidden="true" /> Disimpan saat tugas disimpan</span>
        <span>{wordCount} kata</span>
      </div>
    </div>
  );
}
