import Chat from "@/components/Chat";

export default function Index() {
  return (
    <div className="flex h-dvh min-h-0 flex-col bg-slate-950 text-slate-100">
      <header className="shrink-0 border-b border-slate-800 px-4 py-4 sm:px-8 sm:py-5">
        <div className="mx-auto flex w-full max-w-5xl items-center gap-3">
          <div aria-hidden="true" className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-700 font-bold text-white">EI</div>
          <div>
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl">EI DataBot</h1>
            <p className="text-xs text-slate-400 sm:text-sm">Inteligência analítica para a educação brasileira</p>
          </div>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col p-3 sm:p-6">
        <Chat />
      </main>
      <footer className="shrink-0 px-3 pb-3 text-center text-xs text-slate-500">
        Base analítica educacional · Resultados sujeitos à cobertura dos dados
      </footer>
    </div>
  );
}
