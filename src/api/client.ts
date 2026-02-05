import axios from 'axios';
import { supabase } from '../lib/supabase';

// 创建 axios 实例
// 在开发环境中，Vite 会将 /api 代理到 localhost:8000
const apiClient = axios.create({
  // 生产环境使用完整的后端 URL，开发环境使用 /api 代理
  baseURL: import.meta.env.PROD 
    ? 'https://personal-wealth-management-api.vercel.app/api' 
    : '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加 Auth Token
apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// 响应拦截器
apiClient.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response?.status === 401) {
    // 处理未授权，例如跳转登录（这里由 AuthContext 状态控制）
    console.warn('Unauthorized request');
  }
  return Promise.reject(error);
});

export default apiClient;
