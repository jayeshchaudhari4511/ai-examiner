import axios from 'axios';

const resolveApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  const hostname = window?.location?.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000/api';
  }

  return '/api';
};

const API_BASE_URL = resolveApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes - Gemini vision is much faster than EasyOCR
});

const getStoredTokens = () => {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  return { accessToken, refreshToken };
};

export const setAuthTokens = (accessToken, refreshToken) => {
  if (accessToken) localStorage.setItem('access_token', accessToken);
  if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
};

export const clearAuthTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

api.interceptors.request.use((config) => {
  const { accessToken } = getStoredTokens();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Teacher APIs
export const createTeacher = async (name, email, subject) => {
  const response = await api.post('/teachers', { name, email, subject }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const getTeacher = async (teacherId) => {
  const response = await api.get(`/teachers/${teacherId}`);
  return response.data;
};

export const getAllTeachers = async () => {
  const response = await api.get('/teachers');
  return response.data;
};

export const deleteTeacher = async (teacherId) => {
  const response = await api.delete(`/teachers/${teacherId}`);
  return response.data;
};

// Student APIs
export const createStudent = async (name, email, rollNumber, className) => {
  const response = await api.post('/students', { 
    name, 
    email, 
    roll_number: rollNumber, 
    class: className 
  }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const getStudent = async (studentId) => {
  const response = await api.get(`/students/${studentId}`);
  return response.data;
};

export const getAllStudents = async () => {
  const response = await api.get('/students');
  return response.data;
};

export const deleteStudent = async (studentId) => {
  const response = await api.delete(`/students/${studentId}`);
  return response.data;
};

export const getStudentStatistics = async (studentId) => {
  const response = await api.get(`/students/${studentId}/statistics`);
  return response.data;
};

// Evaluation APIs
export const uploadModelAnswer = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload-model-answer', formData);
  return response.data;
};

export const evaluateAnswer = async (formDataOrFile, modelAnswer, maxMarks, question = '', teacherId = null, studentId = null) => {
  // Handle both FormData object and individual parameters
  let formData;
  
  if (formDataOrFile instanceof FormData) {
    // If FormData is passed directly, use it as-is
    formData = formDataOrFile;
  } else {
    // Otherwise create FormData from individual parameters
    formData = new FormData();
    formData.append('student_file', formDataOrFile);
    formData.append('model_answer', modelAnswer);
    formData.append('max_marks', maxMarks);
    if (question) formData.append('question', question);
    if (teacherId) formData.append('teacher_id', teacherId);
    if (studentId) formData.append('student_id', studentId);
  }
  
  const response = await api.post('/evaluate-answer', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getEvaluation = async (evaluationId) => {
  const response = await api.get(`/evaluations/${evaluationId}`);
  return response.data;
};

export const getEvaluations = async () => {
  const response = await api.get('/evaluations');
  return response.data;
};

export const getStudentEvaluations = async (studentId, limit = 10) => {
  const response = await api.get(`/evaluations/student/${studentId}?limit=${limit}`);
  return response.data;
};

export const getTeacherEvaluations = async (teacherId, limit = 10) => {
  const response = await api.get(`/evaluations/teacher/${teacherId}?limit=${limit}`);
  return response.data;
};

export const getRecentEvaluations = async (limit = 20) => {
  const response = await api.get(`/evaluations/recent?limit=${limit}`);
  return response.data;
};

export const deleteEvaluation = async (evaluationId) => {
  const response = await api.delete(`/evaluations/${evaluationId}`);
  return response.data;
};

export const extractTextOnly = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/ocr-only', formData);
  return response.data;
};

// Auth APIs
export const registerUser = async (payload) => {
  const response = await api.post('/auth/register', payload, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const loginUser = async (email, password) => {
  const response = await api.post('/auth/login', { email, password }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const requestPasswordReset = async (email) => {
  const response = await api.post('/auth/request-reset', { email }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const resetPassword = async (token, newPassword) => {
  const response = await api.post('/auth/reset-password', { token, new_password: newPassword }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Subject APIs
export const createSubject = async (name, code, className) => {
  const response = await api.post('/subjects', { name, code, class: className }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export const getSubjects = async () => {
  const response = await api.get('/subjects');
  return response.data;
};

// Submission APIs
export const createSubmission = async (file, subjectId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('subject_id', subjectId);
  const response = await api.post('/submissions', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getStudentSubmissions = async () => {
  const response = await api.get('/submissions/student');
  return response.data;
};

export const getTeacherSubmissions = async (subjectId) => {
  const response = await api.get(`/submissions/teacher?subject_id=${subjectId}`);
  return response.data;
};

export const evaluateSubmission = async (submissionId, modelAnswer, maxMarks, question = '') => {
  const formData = new FormData();
  formData.append('model_answer', modelAnswer);
  formData.append('max_marks', maxMarks);
  if (question) formData.append('question', question);
  const response = await api.post(`/submissions/${submissionId}/evaluate`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getMyEvaluations = async (limit = 10) => {
  const response = await api.get(`/me/evaluations?limit=${limit}`);
  return response.data;
};

// Admin APIs
export const getPendingTeachers = async () => {
  const response = await api.get('/admin/teachers/pending');
  return response.data;
};

export const approveTeacher = async (teacherId, subjectIds = []) => {
  const response = await api.post(`/admin/teachers/${teacherId}/approve`, { subject_ids: subjectIds }, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
};

export default api;
