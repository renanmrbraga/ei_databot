/** Contrato HTTP do chatbot: o backend é a fonte dos dados e das respostas. */
const API_BASE = "/api";

export type AnalyticValue = string | number | boolean | null;
export type AnalyticRow = Record<string, AnalyticValue>;

export interface ChatResponse {
  resposta: string;
  agente: string;
  fontes: string[];
  cidade: string | null;
  uf: string | null;
  tema: string | null;
  dados_brutos: AnalyticRow[];
  avisos: string[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isAnalyticValue(value: unknown): value is AnalyticValue {
  return value === null || ["string", "number", "boolean"].includes(typeof value);
}

/** Valida a forma do JSON para não apresentar uma resposta incompleta como sucesso. */
export function parseChatResponse(payload: unknown): ChatResponse {
  if (
    !isRecord(payload) ||
    typeof payload.resposta !== "string" ||
    typeof payload.agente !== "string" ||
    !Array.isArray(payload.fontes) ||
    !payload.fontes.every((value) => typeof value === "string") ||
    !Array.isArray(payload.avisos) ||
    !payload.avisos.every((value) => typeof value === "string") ||
    !Array.isArray(payload.dados_brutos) ||
    !payload.dados_brutos.every(
      (row) => isRecord(row) && Object.values(row).every(isAnalyticValue),
    ) ||
    [payload.cidade, payload.uf, payload.tema].some(
      (value) => value !== null && typeof value !== "string",
    )
  ) {
    throw new Error("A API retornou um formato de resposta inesperado.");
  }

  return payload as unknown as ChatResponse;
}

export async function enviarPergunta(
  pergunta: string,
  sessionId: string,
): Promise<ChatResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta, session_id: sessionId }),
    });
  } catch {
    throw new Error("Não foi possível conectar ao backend. Verifique se o FastAPI está ativo.");
  }

  if (!response.ok) {
    if (response.status === 503) {
      throw new Error("O serviço de dados está indisponível. Tente novamente em instantes.");
    }
    if (response.status === 422) {
      throw new Error("A pergunta não foi aceita pelo servidor. Verifique o texto enviado.");
    }
    throw new Error(`Erro HTTP ${response.status} ao consultar o backend.`);
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("O backend não retornou um JSON válido.");
  }
  return parseChatResponse(payload);
}

export interface HistoryMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  warnings?: string[];
}

export function parseHistoryResponse(payload: unknown): HistoryMessage[] {
  if (!isRecord(payload) || !Array.isArray(payload.messages)) {
    throw new Error("Histórico retornado em formato inesperado.");
  }
  const messages = payload.messages;
  if (!messages.every((message: unknown) =>
    isRecord(message) &&
    typeof message.id === "string" &&
    (message.role === "user" || message.role === "assistant") &&
    typeof message.content === "string" &&
    (message.sources === undefined || (Array.isArray(message.sources) && message.sources.every((source) => typeof source === "string"))) &&
    (message.warnings === undefined || (Array.isArray(message.warnings) && message.warnings.every((warning) => typeof warning === "string")))
  )) {
    throw new Error("O histórico contém mensagens inválidas.");
  }
  return messages as HistoryMessage[];
}

export async function carregarHistorico(sessionId: string): Promise<HistoryMessage[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/messages`);
  } catch {
    throw new Error("Não foi possível conectar ao backend para carregar o histórico.");
  }
  if (!response.ok) {
    throw new Error(`Falha HTTP ${response.status} ao carregar o histórico.`);
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("O histórico não contém JSON válido.");
  }
  return parseHistoryResponse(payload);
}


/** Exclui a sessão no PostgreSQL, se presente.
 * Uma sessão comprovadamente ausente pode ser retirada do catálogo local.
 * Falhas de rede e 404 de outras rotas nunca são tratadas como exclusão. */
export async function excluirConversa(sessionId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
    });
  } catch {
    throw new Error("Não foi possível conectar ao backend para excluir a conversa.");
  }
  if (response.status === 204) return;
  if (response.status === 404) {
    // Distingue o 404 de sessão inexistente de uma rota ausente/mal configurada.
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new Error("Erro HTTP 404: não foi possível confirmar a ausência da sessão.");
    }
    if (isRecord(payload) && payload.detail === "Conversa não encontrada.") return;
    throw new Error("Erro HTTP 404 ao excluir a conversa: resposta inesperada da API.");
  }
  throw new Error(`Falha HTTP ${response.status} ao excluir a conversa.`);
}
