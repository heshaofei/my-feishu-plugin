// api.ts
// 后端 API 基础地址
<<<<<<< HEAD
export const API_BASE = 'https://www.canjiu.top/api';
=======
export const API_BASE = 'http://39.105.33.142:8000';
>>>>>>> 20995d9eef52a5e395270eddfc6a202995ea2f56

// 批量处理发票函数
export const processInvoices = async (files: File[], appToken: string, tableId: string) => {
  console.log('API_BASE:', API_BASE);
  console.log('app_token:', appToken);
  console.log('table_id:', tableId);
  
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('app_token', appToken);
  formData.append('table_id', tableId);
  
  try {
    const response = await fetch(`${API_BASE}/process`, {
      method: 'POST',
      body: formData,
    });
    
    const data = await response.json();
    console.log('响应数据:', data);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${data.error || response.statusText}`);
    }
    
    return data;
  } catch (error) {
    console.error('处理发票错误:', error);
    throw error;
  }
};