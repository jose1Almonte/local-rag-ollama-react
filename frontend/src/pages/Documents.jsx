import React, { useEffect, useState } from "react";
import { uploadDocument, listDocuments, indexDocument, deleteDocument } from "../api";
import { FaFilePdf, FaFileWord, FaFileExcel, FaFileAlt, FaFile, FaTrash } from 'react-icons/fa';

export default function Documents(){
  const [file, setFile] = useState(null);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(()=> { refresh(); }, []);

  const refresh = async () => {
    try {
      const r = await listDocuments();
      setDocs(r.data || []);
    } catch(e) {
      console.error(e);
    }
  };

  const handleUpload = async () => {
    if (!file) return alert("Selecciona un archivo");
    setLoading(true);
    try {
      const res = await uploadDocument(file);
      const doc_id = res.data.doc_id;
      // index automatically
      await indexDocument(doc_id, 'name');
      await refresh();
      setFile(null);
      alert("Subido e indexado");
    } catch (e) {
      console.error(e);
      alert("Error al subir");
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async (doc_id) => {
    setLoading(true);
    try {
      await indexDocument(doc_id, 'name');
      alert("Indexado");
      refresh();
    } catch (e) {
      console.error(e);
      alert("Error indexando");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (doc_id) => {
    if(!confirm("Eliminar documento?")) return;
    await deleteDocument(doc_id);
    refresh();
  }
  const getFileType = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    return ext || 'unknown';
  }

  const getFileIcon = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    switch(ext) {
      case 'pdf':
        return { icon: <FaFilePdf  className="w"/>, color: 'text-red-600' };
      case 'doc':
      case 'docx':
        return { icon: <FaFileWord />, color: 'text-blue-600' };
      case 'xls':
      case 'xlsx':
        return { icon: <FaFileExcel />, color: 'text-green-600' };
      case 'txt':
        return { icon: <FaFileAlt />, color: 'text-gray-600' };
      default:
        return { icon: <FaFile />, color: 'text-gray-500' };
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow w-full">
      <h2 className="text-lg font-medium mb-4">Gestión de documentos</h2>

      <div>
        <article className="w-full flex justify-between mb-4 ">
          <h3 className="font-light text-2xl">Documentos</h3>
          <button onClick={handleUpload} disabled={loading || !file} className="bg-blue-200 text-blue-900 hover:border border-blue-900 transition transform px-6 py-2 rounded-xl disabled:bg-gray-400 disabled:cursor-not-allowed">
            Subir e indexar
          </button>
        </article>
        <div 
        className="border-2 border-dashed border-blue-400 bg-blue-50 rounded-lg p-8 mb-4 text-center cursor-pointer hover:bg-blue-100 transition-colors"
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          const droppedFile = e.dataTransfer.files[0];
          if (droppedFile) setFile(droppedFile);
        }}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <input 
          id="fileInput"
          type="file" 
          onChange={(e)=> setFile(e.target.files[0])} 
          className="hidden"
        />
        <div className="text-blue-600 mb-2">
          <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <p className="text-sm text-gray-600">
          {file ? file.name : 'Arrastra un archivo aquí o haz clic para seleccionar'}
        </p>
      </div>
      <h2 className="text-md font-medium mb-4">Todos los archivos</h2>
      <div className="border border-gray-100 rounded-lg">
        {docs.map(d => {
            const { icon, color } = getFileIcon(d.filename);
            const filetype = getFileType(d.filename);
            return (
              <article className="w-full  grid grid-cols-4 gap-4 items-center hover:bg-gray-100 p-4 rounded-lg" key={d.doc_id}>
                <div className={`text-3xl mb-2 ${color}`}>{icon}</div>
                <span className={`font-medium text-sm`}>{d.filename || d.doc_id}</span>
                <div className="bg-gray-100 rounded-2xl text-xs border text-gray-800 border-gray-400 w-fit px-4 py-1">
                  {filetype.toUpperCase()}
                </div>
                <div className="flex gap-2 justify-center">
                  <button onClick={()=> handleIndex(d.filename)} className="text-xs bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded">Indexar</button>
                  <button onClick={()=> handleDelete(d.filename)} className="text-xs bg-red-100 hover:bg-red-200 text-red-600 px-3 py-1 rounded">
                    <FaTrash className="inline"/>
                  </button>
                </div>
              </article>
        )})}

      </div>
      </div>
    </div>
  );
}
