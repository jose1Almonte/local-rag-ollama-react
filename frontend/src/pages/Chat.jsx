import React, { useState } from "react";
import { queryChat } from "../api";
import axios from "axios";
import { FaArrowRight } from "react-icons/fa";

export default function Chat(){
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);

  const suggestedQuestions = [
    "¿Qué información contienen los documentos?",
    "Resume los puntos principales",
    "¿Cuáles son las conclusiones más importantes?"
  ];

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
  };

  const send = async () => {
    if(!query) return;
    const userMsg = {role: "user", text: query};
    setMessages(m => [...m, userMsg]);
    setQuery("");
    try {
      console.log("Querying:", query);
      const res = await queryChat(query);
      const answer = res.data.answer;
      setMessages(m => [...m, {role: "assistant", text: answer}]);
    } catch (e) {
      console.error(e);
      setMessages(m => [...m, {role: "assistant", text: "Error en la consulta"}]);
    }
  }

  return (
    <div className="bg-gray-100 rounded-lg w-full h-[600px] flex flex-col p-8 min-h-screen border border-gray-300">
      <div className="p-4 rounded-t-lg bg-gray-100">
        <h2 className="text-3xl font-regular text-gray-800">Chat con documentos</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-100">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-semibold text-gray-800">Bienvenido al Chat</h3>
              <p className="text-gray-600">Pregunta lo que quieras sobre tus documentos</p>
            </div>
            <div className="flex flex-col gap-3 w-full max-w-md">
              {suggestedQuestions.map((suggestion, i) => (
                <div 
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="p-4 bg-white border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 hover:border-blue-300 transition-all duration-200 shadow-sm"
                >
                  <p className="text-sm text-gray-700">{suggestion}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex w-full ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[70%] p-3 rounded-lg shadow-sm ${
                m.role === 'user' 
                  ? 'bg-blue-100 text-blue-800 rounded-br-none mr-8' 
                  : 'bg-white text-gray-800 rounded-bl-none border border-gray-200 ml-8'
              }`}>
                <div className="text-xs font-semibold mb-1 opacity-75">
                  {m.role === 'user' ? 'Tú' : 'Asistente'}
                </div>
                <div className="text-sm whitespace-pre-wrap">{m.text}</div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 bg-white rounded-lg">
        <div className="flex gap-2">
          <input 
            value={query} 
            onChange={(e)=> setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Pregunta sobre tus documentos..." 
            className="flex-1 border border-gray-100 px-4 py-3 rounded-lg focus:outline-none focus:border-transparent" 
          />
          <button 
            onClick={send} 
            className="bg-blue-200 hover:bg-blue-300 text-blue-800 px-6 py-3 rounded-lg font-medium transition-colors duration-200 shadow-sm"
          >
            <FaArrowRight />
          </button>
        </div>
      </div>
    </div>
  );
}
