import axios from "axios";
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 120000,
});

export const uploadDocument = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
};

export const indexDocument = (doc_id, filename) => api.post(`/index/${doc_id}`, { filename });
export const listDocuments = () => api.get("/documents");
export const deleteDocument = (doc_id) => api.delete(`/documents/${doc_id}`);
export const queryChat = (query) => api.post("/query", { query });
export default api;
