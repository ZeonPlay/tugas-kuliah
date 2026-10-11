import { useEffect, useRef } from "react";
import Editor from "@toast-ui/editor";
import "@toast-ui/editor/dist/toastui-editor.css";
import "@toast-ui/editor/dist/theme/toastui-editor-dark.css";

type MarkdownEditorProps = {
  initialValue: string;
  onChange: (value: string) => void;
};

/**
 * WYSIWYG-first Markdown editor. Saved content remains Markdown so existing
 * task rows and the Streamlit app can continue to consume the same field.
 */
export default function MarkdownEditor({ initialValue, onChange }: MarkdownEditorProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!hostRef.current) return;

    const editor = new Editor({
      el: hostRef.current,
      height: "360px",
      initialValue,
      initialEditType: "wysiwyg",
      previewStyle: "tab",
      theme: "dark",
      language: "en-US",
      usageStatistics: false,
      autofocus: false,
      hideModeSwitch: false,
      placeholder: "Tulis ketentuan tugas di sini. Gunakan toolbar untuk membuat teks tebal, daftar, tautan, atau tabel.",
      toolbarItems: [
        ["heading", "bold", "italic", "strike"],
        ["hr", "quote"],
        ["ul", "ol", "task"],
        ["table", "link"],
      ],
    });

    editor.on("change", () => {
      onChangeRef.current(editor.getMarkdown());
    });

    return () => {
      editor.destroy();
    };
    // The editor is intentionally initialized once per form mount. TaskForm's
    // key changes between create/edit so the correct initial Markdown is loaded.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="toast-editor-shell">
      <div ref={hostRef} aria-label="Editor ketentuan dan instruksi tugas" />
      <p className="field-hint toast-editor-help">
        Mulai dari mode visual. Gunakan tab Markdown jika ingin mengedit sintaks langsung.
      </p>
    </div>
  );
}
