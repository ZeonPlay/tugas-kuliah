import { useRef, useState } from "react";
import type { ReactNode } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "@tiptap/markdown";
import Placeholder from "@tiptap/extension-placeholder";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";

type MarkdownEditorProps = {
  initialValue: string;
  onChange: (value: string) => void;
};

function EditorTool({
  children,
  label,
  active = false,
  onClick,
}: {
  children: ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={"tiptap-tool" + (active ? " is-active" : "")}
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

/**
 * WYSIWYG-first editor. The database value remains Markdown, so the current
 * home-page renderer and existing Streamlit app can continue using the field.
 */
export default function MarkdownEditor({ initialValue, onChange }: MarkdownEditorProps) {
  const onChangeRef = useRef(onChange);
  const [linkError, setLinkError] = useState("");
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
      Table,
      TableRow,
      TableHeader,
      TableCell,
      Markdown.configure({
        markedOptions: { gfm: true },
      }),
      Placeholder.configure({
        placeholder: "Tulis instruksi tugas di sini…",
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
      onChangeRef.current(currentEditor.getMarkdown());
      setLinkError("");
    },
  });

  function insertLink() {
    if (!editor) return;
    setLinkError("");
    const selectedText = !editor.state.selection.empty;
    if (!selectedText) {
      setLinkError("Blok teks yang ingin dijadikan tautan, lalu tekan Tautan.");
      return;
    }

    const currentHref = editor.getAttributes("link").href as string | undefined;
    const input = window.prompt("Masukkan alamat tautan (URL)", currentHref ?? "https://");
    if (input === null) return;

    const href = input.trim();
    if (!href) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
      return;
    }

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

    editor.chain().focus().extendMarkRange("link").setLink({ href }).run();
  }

  return (
    <div className="tiptap-editor-shell">
      <div className="tiptap-toolbar" role="toolbar" aria-label="Pemformatan instruksi">
        {!editor ? (
          <span className="tiptap-toolbar-loading">Menyiapkan editor…</span>
        ) : (
          <>
            <EditorTool label="Tebal" active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}>
              <strong>B</strong>
            </EditorTool>
            <EditorTool label="Miring" active={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()}>
              <em>I</em>
            </EditorTool>
            <EditorTool label="Garis bawah" active={editor.isActive("underline")} onClick={() => editor.chain().focus().toggleUnderline().run()}>
              <span className="tool-underline">U</span>
            </EditorTool>
            <span className="tiptap-toolbar-divider" aria-hidden="true" />
            <EditorTool label="Judul bagian" active={editor.isActive("heading", { level: 2 })} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}>
              H2
            </EditorTool>
            <EditorTool label="Daftar bullet" active={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()}>
              • Daftar
            </EditorTool>
            <EditorTool label="Daftar bernomor" active={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()}>
              1. Daftar
            </EditorTool>
            <EditorTool label="Kutipan" active={editor.isActive("blockquote")} onClick={() => editor.chain().focus().toggleBlockquote().run()}>
              “ Kutipan
            </EditorTool>
            <span className="tiptap-toolbar-divider" aria-hidden="true" />
            <EditorTool label="Tambah tabel 2 kolom" onClick={() => editor.chain().focus().insertTable({ rows: 2, cols: 2, withHeaderRow: true }).run()}>
              Tabel
            </EditorTool>
            <EditorTool label="Sisipkan tautan pada teks terpilih" active={editor.isActive("link")} onClick={insertLink}>
              ↗ Tautan
            </EditorTool>
            <span className="tiptap-toolbar-spacer" />
            <EditorTool label="Batalkan perubahan" onClick={() => editor.chain().focus().undo().run()}>
              ↶
            </EditorTool>
            <EditorTool label="Ulangi perubahan" onClick={() => editor.chain().focus().redo().run()}>
              ↷
            </EditorTool>
          </>
        )}
      </div>
      <EditorContent editor={editor} />
      {linkError && <p className="field-hint field-error tiptap-link-error" role="status">{linkError}</p>}
      <p className="field-hint tiptap-editor-help">
        Ketik seperti dokumen biasa. Format tersimpan sebagai Markdown dan bisa dipakai kembali di aplikasi lama.
      </p>
    </div>
  );
}
