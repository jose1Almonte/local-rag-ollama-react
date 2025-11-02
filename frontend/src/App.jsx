import React, { useState } from "react";
import Documents from "./pages/Documents";
import Chat from "./pages/Chat";
import Lateralbar from "./Lateralbar";

export default function App() {
  const [page, setPage] = useState("docs");
  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* <header className="max-w-5xl mx-auto flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">RAG · Ollama · Chroma</h1>
        <nav className="space-x-4">
          <button onClick={() => setPage("docs")} className="text-sm text-gray-700">Documentos</button>
          <button onClick={() => setPage("chat")} className="text-sm text-gray-700">Chat</button>
        </nav>
      </header> */}

      <main className="w-full mx-aut flex">
        <Lateralbar setPage={setPage} />
        {page === "docs" ? <Documents /> : <Chat />}
      </main>
    </div>
  );
}
