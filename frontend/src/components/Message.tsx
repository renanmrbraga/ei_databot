import type { AnalyticRow, AnalyticValue } from "@/services/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  sources?: string[];
  warnings?: string[];
  data?: AnalyticRow[];
}

const numberFormatter = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 6,
});

function displayValue(value: AnalyticValue, column: string): string {
  if (column === "ano" && typeof value === "number" && Number.isInteger(value)) return String(value);
  if (value === null) return "—";
  if (typeof value === "number") return numberFormatter.format(value);
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  return value;
}

function AnalyticData({ rows }: { rows: AnalyticRow[] }) {
  if (rows.length === 0) return null;
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  if (columns.length === 0) return null;

  return (
    <details className="mt-4 border-t border-white/10 pt-3 text-sm">
      <summary className="cursor-pointer font-medium text-slate-300 hover:text-white">
        Ver dados consultados ({rows.length} {rows.length === 1 ? "registro" : "registros"})
      </summary>
      <div className="mt-3 max-w-full overflow-x-auto rounded-lg border border-white/10">
        <table className="w-full min-w-max border-collapse text-left text-xs">
          <thead className="bg-slate-700/40">
            <tr>
              {columns.map((column) => (
                <th key={column} scope="col" className="px-3 py-2 font-semibold">
                  {column.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-t border-white/10">
                {columns.map((column) => (
                  <td key={column} className="px-3 py-2 tabular-nums">
                    {displayValue(row[column] ?? null, column)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

export default function Message({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <article className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[92%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[85%] sm:px-5 sm:py-4 ${
          isUser
            ? "rounded-br-sm bg-sky-700 text-white"
            : "rounded-bl-sm border border-slate-700/60 bg-slate-800/80 text-slate-100"
        }`}
      >
        {!isUser && (
          <div className="mb-2 text-xs font-semibold tracking-wide text-sky-300">
            {message.agent || "EI DataBot"}
          </div>
        )}
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed sm:text-base">
          {message.content}
        </p>
        {!isUser && message.sources && message.sources.length > 0 && (
          <p className="mt-3 text-xs leading-relaxed text-slate-300">
            <span className="font-semibold">Fontes:</span> {message.sources.join(" · ")}
          </p>
        )}
        {!isUser && message.data && <AnalyticData rows={message.data} />}
        {!isUser && message.warnings && message.warnings.length > 0 && (
          <details className="mt-3 text-xs text-amber-200">
            <summary className="cursor-pointer">Avisos ({message.warnings.length})</summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {message.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </article>
  );
}
