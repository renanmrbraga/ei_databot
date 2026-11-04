import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";

import ts from "typescript";

const source = readFileSync(new URL("../src/services/api.ts", import.meta.url), "utf8");
const { outputText, diagnostics } = ts.transpileModule(source, {
  fileName: "api.ts",
  reportDiagnostics: true,
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
});
assert.deepEqual(diagnostics ?? [], []);

function loadApi(fetchImplementation) {
  const exported = {};
  runInNewContext(outputText, { exports: exported, fetch: fetchImplementation });
  return exported;
}

const { parseChatResponse } = loadApi();

const example = {
  resposta: "Em 2025, houve 56.498 matrículas.",
  agente: "EI DataBot",
  fontes: ["INEP / Censo Escolar"],
  cidade: "Volta Redonda",
  uf: "RJ",
  tema: "educacao_basica",
  dados_brutos: [
    { ano: 2025, matriculas_educacao_basica: 56498, registros_com_valor: 190 },
  ],
  avisos: [],
};

test("aceita o contrato real da API com valores do Gold", () => {
  assert.equal(parseChatResponse(example).dados_brutos[0].matriculas_educacao_basica, 56498);
});

test("preserva os avisos documentais em campo separado", () => {
  const response = parseChatResponse({ ...example, avisos: ["Regra em revisão"] });
  assert.equal(response.resposta, example.resposta);
  assert.equal(response.avisos[0], "Regra em revisão");
});

test("rejeita payloads antigos de gráficos e exportações", () => {
  assert.throws(
    () => parseChatResponse({ resposta: "ok", chart_data: {}, csv_base64: "abc" }),
    /formato de resposta inesperado/,
  );
});

test("rejeita linhas de dados malformadas", () => {
  assert.throws(
    () => parseChatResponse({ ...example, dados_brutos: [{ ano: { invalido: true } }] }),
    /formato de resposta inesperado/,
  );
});


test("envia pergunta e UUID no endpoint /api/chat", async () => {
  let request;
  const { enviarPergunta } = loadApi(async (url, options) => {
    request = { url, ...options };
    return { ok: true, json: async () => example };
  });
  const sessionId = "5f4b8604-7f5c-42a2-8367-2645b3ef6c00";
  const result = await enviarPergunta("Quantas matrículas?", sessionId);
  assert.equal(request.url, "/api/chat");
  assert.equal(request.method, "POST");
  assert.deepEqual(JSON.parse(request.body), {
    pergunta: "Quantas matrículas?",
    session_id: sessionId,
  });
  assert.equal(result.resposta, example.resposta);
});

test("trata indisponibilidade do backend sem fabricar resposta", async () => {
  const { enviarPergunta } = loadApi(async () => ({ ok: false, status: 503 }));
  await assert.rejects(
    enviarPergunta("Pergunta", "uuid"),
    /serviço de dados está indisponível/,
  );
});

test("valida o histórico retornado pelo backend", () => {
  const { parseHistoryResponse } = loadApi();
  const messages = parseHistoryResponse({ messages: [
    { id: "1", role: "user", content: "Pergunta" },
    { id: "2", role: "assistant", content: "Resposta", sources: ["INEP"], warnings: [] },
  ] });
  assert.equal(messages.length, 2);
  assert.equal(messages[1].sources[0], "INEP");
  assert.throws(() => parseHistoryResponse({ messages: [{ role: "assistant" }] }), /inválidas/);
});

test("consulta o histórico da sessão pela API", async () => {
  let requestUrl;
  const { carregarHistorico } = loadApi(async (url) => {
    requestUrl = url;
    return { ok: true, json: async () => ({ messages: [] }) };
  });
  const messages = await carregarHistorico("5f4b8604-7f5c-42a2-8367-2645b3ef6c00");
  assert.equal(requestUrl, "/api/sessions/5f4b8604-7f5c-42a2-8367-2645b3ef6c00/messages");
  assert.equal(messages.length, 0);
});


test("exclui conversa somente com HTTP 204", async () => {
  let request;
  const { excluirConversa } = loadApi(async (url, options) => {
    request = { url, ...options };
    return { status: 204 };
  });
  await excluirConversa("5f4b8604-7f5c-42a2-8367-2645b3ef6c00");
  assert.equal(request.url, "/api/sessions/5f4b8604-7f5c-42a2-8367-2645b3ef6c00");
  assert.equal(request.method, "DELETE");
});

test("falha de exclusão não é tratada como sucesso", async () => {
  const { excluirConversa } = loadApi(async () => ({ status: 503 }));
  await assert.rejects(excluirConversa("uuid"), /Falha HTTP 503/);
});


test("remove referência local quando a sessão não existe no PostgreSQL", async () => {
  const { excluirConversa } = loadApi(async () => ({
    status: 404,
    json: async () => ({ detail: "Conversa não encontrada." }),
  }));
  await excluirConversa("uuid-de-sessao-orfa");
});

test("não trata 404 de rota desconhecida como exclusão válida", async () => {
  const { excluirConversa } = loadApi(async () => ({
    status: 404,
    json: async () => ({ detail: "Not Found" }),
  }));
  await assert.rejects(excluirConversa("uuid"), /resposta inesperada da API/);
});

test("não trata erro de conexão como exclusão", async () => {
  const { excluirConversa } = loadApi(async () => { throw new Error("offline"); });
  await assert.rejects(excluirConversa("uuid"), /Não foi possível conectar/);
});
