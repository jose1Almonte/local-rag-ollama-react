import React, { useEffect, useState } from "react";
import { uploadDocuments, listDocuments, indexDocument, deleteDocument, checkIndexed } from "../api";
import { FaFilePdf, FaFileWord, FaFileExcel, FaFileAlt, FaFile, FaTrash } from 'react-icons/fa';

export default function Documents(){
  const [files, setFiles] = useState([]);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [indexedStatus, setIndexedStatus] = useState({});

  useEffect(()=> { refresh(); }, []);

  const refresh = async () => {
    try {
      const r = await listDocuments();
      const docsList = r.data || [];
      setDocs(docsList);
      
      // Check indexed status for each document
      const statusPromises = docsList.map(async (d) => {
        try {
          const res = await checkIndexed(d.doc_id);
          return { doc_id: d.doc_id, indexed: res.data.indexed, chunks: res.data.chunks };
        } catch {
          return { doc_id: d.doc_id, indexed: false, chunks: 0 };
        }
      });
      
      const statuses = await Promise.all(statusPromises);
      const statusMap = {};
      statuses.forEach(s => {
        statusMap[s.doc_id] = { indexed: s.indexed, chunks: s.chunks };
      });
      setIndexedStatus(statusMap);
    } catch(e) {
      console.error(e);
    }
  };

  const handleUpload = async () => {
    if (!files.length) return alert("Selecciona al menos un archivo");
    setLoading(true);
    setUploadProgress(`Subiendo 0 de ${files.length}...`);
    try {
      const res = await uploadDocuments(files);
      const uploaded = res.data.uploaded || [];
      setUploadProgress(`Indexando 0 de ${uploaded.length}...`);
      for (let i = 0; i < uploaded.length; i++) {
        setUploadProgress(`Indexando ${i + 1} de ${uploaded.length}...`);
        await indexDocument(uploaded[i].doc_id, 'name');
      }
      await refresh();
      setFiles([]);
      setUploadProgress("");
      alert(`${uploaded.length} archivo(s) subido(s) e indexado(s)`);
    } catch (e) {
      console.error(e);
      alert("Error al subir");
    } finally {
      setLoading(false);
      setUploadProgress("");
    }
  };

  const handleIndex = async (doc_id) => {
    setLoading(true);
    try {
      const isIndexed = indexedStatus[doc_id]?.indexed;
      await indexDocument(doc_id, doc_id);
      alert(isIndexed ? "Re-indexado" : "Indexado");
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
  const addFiles = (newFiles) => {
    const fileArray = Array.from(newFiles);
    setFiles(prev => [...prev, ...fileArray]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

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
          <button onClick={handleUpload} disabled={loading || !files.length} className="bg-blue-200 text-blue-900 hover:border border-blue-900 transition transform px-6 py-2 rounded-xl disabled:bg-gray-400 disabled:cursor-not-allowed cursor-pointer">
            {loading ? uploadProgress : `Subir e indexar (${files.length})`}
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
          addFiles(e.dataTransfer.files);
        }}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <input 
          id="fileInput"
          type="file" 
          multiple
          onChange={(e)=> addFiles(e.target.files)} 
          className="hidden"
        />
        <div className="text-blue-600 mb-2">
          <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <p className="text-sm text-gray-600">
          {files.length > 0 ? `${files.length} archivo(s) seleccionado(s)` : 'Arrastra archivos aquí o haz clic para seleccionar (múltiple)'}
        </p>
      </div>
      {files.length > 0 && (
        <div className="mb-4 space-y-1">
          {files.map((f, i) => (
            <div key={i} className="flex items-center justify-between bg-gray-50 rounded px-3 py-1 text-sm">
              <span className="truncate">{f.name}</span>
              <button onClick={() => removeFile(i)} className="text-red-500 hover:text-red-700 ml-2 cursor-pointer">✕</button>
            </div>
          ))}
        </div>
      )}
      <h2 className="text-md font-medium mb-4">Todos los archivos</h2>
      <div className="border border-gray-100 rounded-lg">
        {docs.map(d => {
            const { icon, color } = getFileIcon(d.filename);
            const filetype = getFileType(d.filename);
            const doc_id = d.doc_id;
            const isIndexed = indexedStatus[doc_id]?.indexed;
            const chunks = indexedStatus[doc_id]?.chunks || 0;
            return (
              <article className="w-full  grid grid-cols-4 gap-4 items-center hover:bg-gray-100 p-4 rounded-lg" key={d.doc_id}>
                <div className={`text-3xl mb-2 ${color}`}>{icon}</div>
                <div className="flex flex-col">
                  <span className={`font-medium text-sm`}>{d.filename}</span>
                  {isIndexed && (
                    <span className="text-xs text-green-600 mt-1">Indexado ({chunks} chunks)</span>
                  )}
                </div>
                <div className="bg-gray-100 rounded-2xl text-xs border text-gray-800 border-gray-400 w-fit px-4 py-1">
                  {filetype.toUpperCase()}
                </div>
                <div className="flex gap-2 justify-center">
                  <button 
                    onClick={()=> handleIndex(d.doc_id)} 
                    className={`text-xs px-3 py-1 rounded cursor-pointer ${
                      isIndexed 
                        ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-800' 
                        : 'bg-gray-200 hover:bg-gray-300'
                    }`}
                  >
                    {isIndexed ? 'Re-indexar' : 'Indexar'}
                  </button>
                  <button onClick={()=> handleDelete(d.doc_id)} className="text-xs bg-red-100 hover:bg-red-200 text-red-600 px-3 py-1 rounded cursor-pointer">
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
