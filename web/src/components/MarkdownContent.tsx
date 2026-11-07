import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

/**
 * Old instructions were sometimes stored with Markdown punctuation escaped
 * (for example, `**UTS\\_NAMA\\_KELAS.pdf**`). Those slashes stop the Markdown
 * syntax from behaving as intended. Normalize only common Markdown markers
 * before parsing; ReactMarkdown still renders HTML as text rather than trusting it.
 */
export function normalizeLegacyMarkdown(value: string): string {
  return value
    .replace(/\\([*_~])/g, "$1")
    .replace(/\r\n?/g, "\n")
    .trim();
}

export default function MarkdownContent({ content, className }: MarkdownContentProps) {
  const source = normalizeLegacyMarkdown(content);

  if (!source) return null;

  return (
    <div className={["markdown-content", className].filter(Boolean).join(" ")}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{source}</ReactMarkdown>
    </div>
  );
}
