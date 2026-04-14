import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { bitable } from '@lark-base-open/js-sdk';
import { Toast, Button, Card, Space, Upload, Tag, Progress, Input } from '@douyinfe/semi-ui';
import { IconUpload } from '@douyinfe/semi-icons';
import { processInvoices } from './api';
import './index.css';

// ========== 类型定义 ==========
interface FileItem {
  file: File;
  id: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  previewUrl?: string;
  result?: any;
}

// URL 解析结果类型
interface ParsedUrlInfo {
  fullUrl: string;      // 完整URL
  domain: string;       // 域名
  appToken: string;     // app_token
  tableId: string;      // table_id
}

const App: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  
  // 表格连接相关状态
  const [tableUrl, setTableUrl] = useState<string>('');
  const [domain, setDomain] = useState<string>('');
  const [appToken, setAppToken] = useState<string>('');
  const [tableId, setTableId] = useState<string>('');
  const [isTableSelected, setIsTableSelected] = useState<boolean>(false);
  const [urlError, setUrlError] = useState<string>('');

  /**
   * 解析飞书多维表格 URL
   * URL 格式: https://{domain}.feishu.cn/base/{app_token}?table={table_id}
   */
  const parseFeishuUrl = (url: string): ParsedUrlInfo | null => {
    try {
      // 正则匹配各个部分
      // 匹配域名: https://xxx.feishu.cn 或 https://xxx.larksuite.com
      const domainMatch = url.match(/https?:\/\/([^\/]+)/);
      // 匹配 app_token: /base/后面的部分
      const appTokenMatch = url.match(/\/base\/([^/?]+)/);
      // 匹配 table_id: table=后面的部分
      const tableIdMatch = url.match(/[?&]table=([^&]+)/);
      
      if (!domainMatch || !appTokenMatch || !tableIdMatch) {
        return null;
      }
      
      return {
        fullUrl: url,
        domain: domainMatch[1],
        appToken: appTokenMatch[1],
        tableId: tableIdMatch[1]
      };
    } catch (error) {
      console.error('URL 解析失败:', error);
      return null;
    }
  };

  /**
   * 处理用户输入的表格 URL
   */
  const handleUrlChange = (value: string) => {
    setTableUrl(value);
    setUrlError('');
    
    if (!value.trim()) {
      setIsTableSelected(false);
      setDomain('');
      setAppToken('');
      setTableId('');
      return;
    }
    
    const parsed = parseFeishuUrl(value);
    if (parsed) {
      setDomain(parsed.domain);
      setAppToken(parsed.appToken);
      setTableId(parsed.tableId);
      setIsTableSelected(true);
      setUrlError('');
      Toast.success('表格信息解析成功！');
      console.log('解析结果:', parsed);
    } else {
      setIsTableSelected(false);
      setUrlError('URL 格式不正确，请检查后重试');
    }
  };

  /**
   * 自动获取当前表格 URL（通过飞书 SDK）
   */
  const autoDetectUrl = async () => {
    try {
      // 方法1：尝试获取父页面 URL
      let detectedUrl = '';
      try {
        detectedUrl = window.parent.location.href;
      } catch (e) {
        // 跨域时使用 referrer
        detectedUrl = document.referrer;
      }
      
      if (detectedUrl && detectedUrl.includes('/base/')) {
        setTableUrl(detectedUrl);
        const parsed = parseFeishuUrl(detectedUrl);
        if (parsed) {
          setDomain(parsed.domain);
          setAppToken(parsed.appToken);
          setTableId(parsed.tableId);
          setIsTableSelected(true);
          Toast.success('自动获取表格信息成功！');
        } else {
          Toast.warning('自动获取失败，请手动输入');
        }
      } else {
        Toast.warning('无法自动获取，请手动输入表格链接');
      }
    } catch (error) {
      console.error('自动获取失败:', error);
      Toast.warning('自动获取失败，请手动输入');
    }
  };

  // 组件加载时尝试自动获取
  useEffect(() => {
    autoDetectUrl();
  }, []);

  /**
   * 处理文件上传
   */
  const handleUpload = (fileList: File[]) => {
    const newFiles: FileItem[] = fileList.map(file => ({
      file,
      id: `${Date.now()}_${Math.random()}`,
      status: 'pending',
      previewUrl: URL.createObjectURL(file),
      result: undefined,
    }));
    setFiles(prev => [...prev, ...newFiles]);
    Toast.success(`已添加 ${fileList.length} 个文件`);
  };

  /**
   * 清空所有文件
   */
  const handleClear = () => {
    files.forEach(file => {
      if (file.previewUrl) {
        URL.revokeObjectURL(file.previewUrl);
      }
    });
    setFiles([]);
    setProgress(0);
  };

  /**
   * 批量处理发票
   */
  const handleProcess = async () => {
    if (files.length === 0) {
      Toast.warning('请先上传发票图片');
      return;
    }

    if (!isTableSelected || !appToken || !tableId) {
      Toast.warning('请先正确填写多维表格链接');
      return;
    }

    setProcessing(true);
    setProgress(0);
    setFiles(prev => prev.map(f => ({ ...f, status: 'processing' })));

    try {
      // 调用后端 API，传递 app_token 和 table_id
      const result = await processInvoices(
        files.map(f => f.file), 
        appToken, 
        tableId
      );
      
      console.log('处理结果:', result);
      
      if (result && result.success === true) {
        setFiles(prev => prev.map((file, idx) => {
          const fileResult = result.results?.[idx];
          return {
            ...file,
            status: fileResult?.status === 'success' ? 'success' : 'error',
            result: fileResult
          };
        }));
        setProgress(100);
        Toast.success(`处理完成：成功 ${result.success_count}，失败 ${result.fail_count}`);
      } else {
        const errorMsg = result?.error || result?.message || '处理失败';
        throw new Error(errorMsg);
      }
      
    } catch (error) {
      console.error('处理失败:', error);
      Toast.error('处理失败，请检查后端服务是否启动');
      setFiles(prev => prev.map(f => ({ ...f, status: 'error' })));
    } finally {
      setProcessing(false);
    }
  };

  /**
   * 组件卸载时清理预览URL
   */
  useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.previewUrl) {
          URL.revokeObjectURL(file.previewUrl);
        }
      });
    };
  }, [files]);

  return (
    <div style={{ padding: '20px' }}>
      <Card title="发票识别与导入" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <Space vertical style={{ width: '100%' }} spacing="large">
          
          {/* 表格链接输入区域 */}
          <div>
            <div style={{ marginBottom: '8px', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>飞书多维表格链接：</span>
              <Button size="small" onClick={autoDetectUrl} disabled={processing}>
                自动获取
              </Button>
            </div>
            <Input
              placeholder="请输入飞书多维表格的完整URL，例如：https://xxx.feishu.cn/base/xxxxx?table=xxxxx"
              value={tableUrl}
              onChange={handleUrlChange}
              disabled={processing}
            />
            {urlError && (
              <div style={{ fontSize: '12px', color: '#ff4d4f', marginTop: '4px' }}>
                ⚠️ {urlError}
              </div>
            )}
            <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
              💡 获取方法：打开飞书多维表格 → 复制浏览器地址栏完整URL
            </div>
          </div>

          {/* 解析结果显示 */}
          {isTableSelected && (
            <div style={{ 
              padding: '12px', 
              background: '#e8f5e9', 
              borderRadius: '8px',
              fontSize: '12px'
            }}>
              <div><strong>✅ 表格连接成功</strong></div>
              <div style={{ marginTop: '4px', color: '#666' }}>
                <div>域名：{domain}</div>
                <div>app_token：{appToken}</div>
                <div>table_id：{tableId}</div>
              </div>
            </div>
          )}

          {/* 未连接提示 */}
          {!isTableSelected && tableUrl && !urlError && (
            <div style={{ 
              padding: '12px', 
              background: '#fff3e0', 
              borderRadius: '8px',
              fontSize: '12px',
              color: '#ed6c02'
            }}>
              ⚠️ 正在解析表格链接...
            </div>
          )}

          {/* 上传区域 */}
          <Upload
            accept="image/*"
            multiple
            onFileChange={handleUpload}
            drag
            disabled={processing}
            action=""
            autoUpload={false}
            uploadTrigger="custom"
          >
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <IconUpload size="large" />
              <p>点击或拖拽上传发票图片</p>
              <p style={{ fontSize: '12px', color: '#999' }}>支持 JPG、PNG 格式</p>
            </div>
          </Upload>

          {/* 文件列表 */}
          {files.length > 0 && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span>已上传 {files.length} 张发票</span>
                <Button size="small" onClick={handleClear} disabled={processing}>
                  清空
                </Button>
              </div>
              <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                {files.map((file) => (
                  <div key={file.id} style={{ 
                    padding: '8px', 
                    borderBottom: '1px solid #eee',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {file.file.name}
                    </span>
                    <Tag color={
                      file.status === 'success' ? 'green' :
                      file.status === 'error' ? 'red' :
                      file.status === 'processing' ? 'blue' : 'grey'
                    }>
                      {file.status === 'success' ? '成功' :
                       file.status === 'error' ? '失败' :
                       file.status === 'processing' ? '处理中' : '等待'}
                    </Tag>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 进度条 */}
          {processing && (
            <div>
              <Progress percent={progress} />
              <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '12px', color: '#666' }}>
                正在处理 {files.filter(f => f.status === 'processing').length} / {files.length} 张发票...
              </div>
            </div>
          )}

          {/* 处理按钮 */}
          <Button
            type="primary"
            onClick={handleProcess}
            loading={processing}
            disabled={files.length === 0 || !isTableSelected}
            style={{ width: '100%', height: '40px' }}
          >
            {processing ? '处理中...' : `开始识别并导入 (${files.length}张)`}
          </Button>

          {/* 使用说明 */}
          <div style={{ 
            fontSize: '12px', 
            color: '#999', 
            paddingTop: '12px',
            borderTop: '1px solid #eee'
          }}>
            <div>💡 使用说明：</div>
            <div>1. 输入或粘贴飞书多维表格的完整链接</div>
            <div>2. 上传发票图片（支持批量上传）</div>
            <div>3. 点击"开始识别并导入"按钮</div>
            <div>4. 系统会自动识别发票信息并写入多维表格</div>
          </div>
        </Space>
      </Card>
    </div>
  );
};

// 渲染应用
const root = createRoot(document.getElementById('root')!);
root.render(<App />);

export default App;