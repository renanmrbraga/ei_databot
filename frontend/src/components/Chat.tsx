import { History, Plus, Send, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { carregarHistorico, enviarPergunta, excluirConversa } from "@/services/api";
import Message from "./Message";
import type { ChatMessage } from "./Message";

interface ChatSession {
  sessionId: string;
  messages: ChatMessage[];
}

interface SessionEntry {
  id: string;
  title: string;
}

const STORAGE_KEY = "ei_databot_chat_v1";
const HISTORY_KEY = "ei_databot_sessions_v1";
const ACTIVE_KEY = "ei_databot_active_session_v1";
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function createSession(): ChatSession {
  return { sessionId: crypto.randomUUID(), messages: [] };
}

function restoreRegistry(): SessionEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const value: unknown = raw ? JSON.parse(raw) : [];
    if (Array.isArray(value)) {
      return value.filter((item: unknown): item is SessionEntry =>
        typeof item === "object" && item !== null && "id" in item &&
        "title" in item && typeof item.id === "string" && UUID_PATTERN.test(item.id) &&
        typeof item.title === "string",
      ).slice(0, 50);
    }
  } catch { /* armazenamento indisponível */ }
  return [];
}

function restoreSession(): ChatSession {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const value: unknown = JSON.parse(raw);
      if (typeof value === "object" && value !== null && "sessionId" in value &&
          "messages" in value && typeof value.sessionId === "string" &&
          UUID_PATTERN.test(value.sessionId) && Array.isArray(value.messages)) {
        return { sessionId: value.sessionId, messages: value.messages as ChatMessage[] };
      }
    }
    const lastId = localStorage.getItem(ACTIVE_KEY);
    if (lastId && UUID_PATTERN.test(lastId)) return { sessionId: lastId, messages: [] };
  } catch { /* armazenamento indisponível */ }
  return createSession();
}

function shortTitle(question: string): string {
  return question.trim().replace(/\s+/g, " ").slice(0, 68);
}

export default function Chat() {
  const [session, setSession] = useState<ChatSession>(restoreSession);
  const [registry, setRegistry] = useState<SessionEntry[]>(() => {
    const previous = restoreRegistry();
    const last = restoreSession();
    if (last.messages.length > 0 && !previous.some((item) => item.id === last.sessionId)) {
      const question = last.messages.find((item) => item.role === "user")?.content;
      if (question) return [{ id: last.sessionId, title: shortTitle(question) }, ...previous].slice(0, 50);
    }
    return previous;
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sendingRef = useRef(false);
  const [pendingRestore, setPendingRestore] = useState(() => {
    const initial = restoreSession();
    return initial.messages.length === 0 && restoreRegistry().some((item) => item.id === initial.sessionId)
      ? initial.sessionId : null;
  });
  const activeRequest = useRef(0);

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        ...session,
        messages: session.messages.slice(0, session.messages.length - session.messages.length % 2).slice(-100),
      }));
      localStorage.setItem(ACTIVE_KEY, session.sessionId);
    } catch { /* funcionamento temporário se storage estiver bloqueado */ }
  }, [session]);

  useEffect(() => {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(registry)); }
    catch { /* funcionamento temporário se storage estiver bloqueado */ }
  }, [registry]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session.messages, loading]);

  // Se a aba foi reaberta, recarrega do PostgreSQL usando o UUID local.
  useEffect(() => {
    if (!pendingRestore) return;
    let cancelled = false;
    void carregarHistorico(pendingRestore).then((messages) => {
      if (!cancelled) setSession({ sessionId: pendingRestore, messages });
    }).catch((cause: unknown) => {
      if (!cancelled) setError(cause instanceof Error ? cause.message : "Falha ao recuperar conversa.");
    }).finally(() => {
      if (!cancelled) setPendingRestore(null);
    });
    return () => { cancelled = true; };
  }, [pendingRestore]);

  async function openSession(id: string) {
    if (sendingRef.current || loadingHistory || pendingRestore || deletingId) return;
    const ticket = ++activeRequest.current;
    setLoadingHistory(true);
    setError(null);
    try {
      const messages = await carregarHistorico(id);
      if (ticket !== activeRequest.current) return;
      setSession({ sessionId: id, messages });
    } catch (cause) {
      if (ticket === activeRequest.current) {
        setError(cause instanceof Error ? cause.message : "Falha ao recuperar conversa.");
      }
    } finally {
      if (ticket === activeRequest.current) setLoadingHistory(false);
    }
  }

  async function handleSend() {
    const question = input.trim();
    if (!question || sendingRef.current || loadingHistory || pendingRestore || deletingId) return;
    sendingRef.current = true;
    setLoading(true);
    setError(null);
    setInput("");
    const currentId = session.sessionId;
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question };
    setSession((previous) => ({ ...previous, messages: [...previous.messages, userMessage] }));
    try {
      const response = await enviarPergunta(question, currentId);
      setSession((previous) => ({
        ...previous,
        messages: [...previous.messages, {
          id: crypto.randomUUID(), role: "assistant", content: response.resposta,
          agent: response.agente, sources: response.fontes,
          warnings: response.avisos, data: response.dados_brutos,
        }],
      }));
      setRegistry((previous) => {
        const existing = previous.find((item) => item.id === currentId);
        return [{ id: currentId, title: existing?.title ?? shortTitle(question) },
          ...previous.filter((item) => item.id !== currentId)].slice(0, 50);
      });
    } catch (cause) {
      setSession((previous) => ({ ...previous,
        messages: previous.messages.filter((message) => message.id !== userMessage.id),
      }));
      setInput((previous) => previous || question);
      setError(cause instanceof Error ? cause.message : "Falha inesperada na consulta.");
    } finally {
      sendingRef.current = false;
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  async function handleDelete(entry: SessionEntry) {
    if (sendingRef.current || loadingHistory || pendingRestore || deletingId) return;
    if (!window.confirm(`Excluir definitivamente a conversa "${entry.title}"? Essa ação não pode ser desfeita.`)) return;
    setDeletingId(entry.id);
    setError(null);
    try {
      await excluirConversa(entry.id);
      setRegistry((previous) => previous.filter((item) => item.id !== entry.id));
      if (entry.id === session.sessionId) {
        activeRequest.current += 1;
        setSession(createSession());
        setInput("");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Falha ao excluir a conversa.");
    } finally {
      setDeletingId(null);
    }
  }

  function newConversation() {
    if (sendingRef.current || loadingHistory || pendingRestore || deletingId) return;
    activeRequest.current += 1;
    setSession(createSession());
    setInput("");
    setError(null);
    inputRef.current?.focus();
  }

  return (
    <section aria-label="Conversa com o EI DataBot" className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/50 shadow-xl md:flex-row">
      <aside aria-label="Histórico de conversas" className="flex max-h-48 shrink-0 flex-col border-b border-slate-700/60 bg-slate-950/50 md:max-h-none md:w-60 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between border-b border-slate-700/60 px-3 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200"><History size={16} /> Conversas</div>
          <button type="button" onClick={newConversation} disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null} aria-label="Nova conversa" title="Nova conversa"
            className="rounded-md p-2 text-slate-200 hover:bg-slate-800 disabled:opacity-50"><Plus size={18} /></button>
        </div>
        <nav className="min-h-0 overflow-y-auto p-2" aria-label="Conversas recentes">
          {registry.length === 0 && <p className="px-2 py-3 text-xs text-slate-400">Suas conversas aparecerão aqui.</p>}
          {registry.map((entry) => (
            <div key={entry.id} className={`mb-1 flex items-center gap-1 rounded-lg hover:bg-slate-800 ${entry.id === session.sessionId ? "bg-sky-900/50" : ""}`}>
              <button type="button" disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null}
                aria-current={entry.id === session.sessionId ? "page" : undefined}
                onClick={() => { if (entry.id !== session.sessionId) void openSession(entry.id); }}
                className={`min-w-0 flex-1 truncate rounded-lg px-3 py-2 text-left text-xs disabled:opacity-50 ${entry.id === session.sessionId ? "text-sky-100" : "text-slate-300"}`}
                title={entry.title}>{entry.title}</button>
              <button type="button" disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null}
                aria-label={`Excluir conversa: ${entry.title}`} title="Excluir conversa definitivamente"
                onClick={() => { void handleDelete(entry); }}
                className="mr-1 shrink-0 rounded-md p-2 text-slate-400 hover:bg-rose-950/70 hover:text-rose-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-rose-400 disabled:opacity-50">
                <Trash2 size={15} aria-hidden="true" />
              </button>
            </div>
          ))}
        </nav>
      </aside>
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-slate-700/60 px-4 py-3 sm:px-6">
          <div><h2 className="text-sm font-semibold text-slate-100">Conversa</h2><p className="text-xs text-slate-400">Perguntas sobre indicadores educacionais</p></div>
          <button type="button" onClick={newConversation} disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null}
            className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50"><Plus size={14} /> Nova conversa</button>
        </div>
        <div role="log" aria-label="Mensagens do chat" className="chat-messages min-h-0 flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
          {(loadingHistory || pendingRestore) && <p role="status" className="text-sm text-slate-400">Recuperando conversa...</p>}
          {!loadingHistory && !pendingRestore && session.messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 px-4 py-3 text-2xl" aria-hidden="true">✦</div>
              <p className="max-w-md text-base font-medium text-slate-100">Como posso ajudar com os dados educacionais?</p>
              <p className="max-w-md text-sm text-slate-400">Exemplo: Quantas matrículas da educação básica houve em Volta Redonda/RJ em 2025?</p>
            </div>
          )}
          {!loadingHistory && !pendingRestore && session.messages.map((message) => <Message key={message.id} message={message} />)}
          {loading && <p role="status" className="text-sm text-slate-400">Consultando dados e preparando resposta...</p>}
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t border-slate-700/60 bg-slate-900/80 p-4 sm:p-5">
          {error && <p role="alert" className="mb-3 rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-100">{error}</p>}
          <form onSubmit={(event) => { event.preventDefault(); void handleSend(); }} className="mx-auto flex w-full max-w-4xl items-end gap-2">
            <label htmlFor="chat-question" className="sr-only">Pergunta</label>
            <textarea id="chat-question" ref={inputRef} autoFocus rows={2} maxLength={2000}
              placeholder="Digite sua pergunta..." value={input} onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void handleSend(); } }}
              disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null}
              className="min-h-12 max-h-40 min-w-0 flex-1 resize-y rounded-xl border border-slate-600 bg-slate-800/90 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-400 focus-visible:border-sky-400 sm:text-base" />
            <button type="submit" aria-label="Enviar pergunta" disabled={loading || loadingHistory || pendingRestore !== null || deletingId !== null || input.trim().length === 0}
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-50"><Send size={20} /></button>
          </form>
          <p className="mt-2 text-center text-xs text-slate-500">Enter envia · Shift+Enter quebra linha · Dados: INEP</p>
        </div>
      </div>
    </section>
  );
}
