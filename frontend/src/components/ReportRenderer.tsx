import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface Props {
  markdown: string;
}

export default function ReportRenderer({ markdown }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      <article className="prose prose-invert prose-sm max-w-none
                          prose-headings:text-gray-100 prose-p:text-gray-300
                          prose-strong:text-gray-100 prose-li:text-gray-300
                          prose-a:text-indigo-400">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {markdown}
        </ReactMarkdown>
      </article>
    </div>
  );
}
