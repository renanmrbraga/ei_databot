export default function NotFound() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-slate-950 px-4 text-center text-slate-100">
      <h1 className="text-5xl font-bold">404</h1>
      <p className="text-slate-400">Página não encontrada.</p>
      <a href="/" className="rounded-lg bg-sky-700 px-4 py-2 hover:bg-sky-600">Voltar ao EI DataBot</a>
    </main>
  );
}
