import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

export default function MarkdownContent({ content, className }: MarkdownContentProps) {
  const source = content.trim();

  if (!source) return null;

  return (
    <div className={["markdown-content", className].filter(Boolean).join(" ")}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{source}</ReactMarkdown>
    </div>
  );
}
