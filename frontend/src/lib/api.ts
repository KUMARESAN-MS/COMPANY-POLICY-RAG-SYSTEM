import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
});

// ── Token Management ────────────────────────────────────────────
const TOKEN_KEY = 'policyguard_token';

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const removeToken = () => localStorage.removeItem(TOKEN_KEY);

// ── Axios Interceptor: attach token to every request ────────────
client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth API ────────────────────────────────────────────────────
export interface AuthResponse {
  token: string;
  username: string;
  role: string;
}

export const signup = async (
  username: string,
  password: string,
  role: string = 'employee',
  admin_secret?: string
): Promise<AuthResponse> => {
  const { data } = await client.post('/auth/signup', {
    username,
    password,
    role,
    admin_secret,
  });
  return data;
};

export const login = async (username: string, password: string): Promise<AuthResponse> => {
  const { data } = await client.post('/auth/login', { username, password });
  return data;
};

export const getMe = async (): Promise<{ username: string; role: string }> => {
  const { data } = await client.get('/auth/me');
  return data;
};

// ── Existing API ────────────────────────────────────────────────
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
