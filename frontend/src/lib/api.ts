import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
});

export interface Document {
  id: number;
  filename: string;
  upload_time: string;
  is_deleted: boolean;
}

export interface Source {
  filename: string;
  page: number;
  text: string;
  score: number;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
}

export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

export const askQuestion = async (question: string, top_k: number = 5): Promise<AskResponse> => {
  const { data } = await client.post('/ask', { question, top_k });
  return data;
};

export const listDocuments = async () => {
  const { data } = await client.get('/documents');
  return data;
};

export const deleteDocument = async (docId: number) => {
  const { data } = await client.delete(`/documents/${docId}`);
  return data;
};

export const checkHealth = async () => {
  const { data } = await client.get('/health');
  return data;
};
