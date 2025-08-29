// 格式化文件大小
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 格式化时间
export const formatTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// 格式化日期
export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 复制到剪贴板
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // 降级方案
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch (err) {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

// 从剪贴板读取
export const readFromClipboard = async (): Promise<string | null> => {
  try {
    const text = await navigator.clipboard.readText();
    return text;
  } catch (err) {
    return null;
  }
};

// 验证URL
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// 验证邮箱
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// 检测视频平台
export const detectPlatform = (url: string): string => {
  if (url.includes('douyin.com') || url.includes('dy.com')) return '抖音';
  if (url.includes('kuaishou.com') || url.includes('ks.com')) return '快手';
  if (url.includes('xiaohongshu.com') || url.includes('xhs.com')) return '小红书';
  if (url.includes('weixin.qq.com') || url.includes('mp.weixin.qq.com')) return '视频号';
  if (url.includes('bilibili.com') || url.includes('b23.tv')) return 'B站';
  if (url.includes('tiktok.com')) return 'Tiktok';
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube';
  return '其他';
};

// 获取平台图标类名
export const getPlatformIcon = (platform: string): string => {
  switch (platform) {
    case '抖音': return 'fab fa-tiktok';
    case '快手': return 'fas fa-play';
    case '小红书': return 'fas fa-book';
    case '视频号': return 'fab fa-weixin';
    case 'B站': return 'fas fa-b';
    case 'Tiktok': return 'fab fa-tiktok';
    case 'YouTube': return 'fab fa-youtube';
    default: return 'fas fa-globe';
  }
};

// 获取平台颜色类名
export const getPlatformColor = (platform: string): string => {
  switch (platform) {
    case '抖音': return 'bg-pink-100 text-pink-800';
    case '快手': return 'bg-yellow-100 text-yellow-800';
    case '小红书': return 'bg-red-100 text-red-800';
    case '视频号': return 'bg-green-100 text-green-800';
    case 'B站': return 'bg-blue-100 text-blue-800';
    case 'Tiktok': return 'bg-gray-100 text-gray-800';
    case 'YouTube': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// 生成随机ID
export const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// 防抖函数
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// 节流函数
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// 深拷贝
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
};

// 获取文件扩展名
export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
};

// 检查是否为视频文件
export const isVideoFile = (filename: string): boolean => {
  const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp', 'm4v'];
  const extension = getFileExtension(filename).toLowerCase();
  return videoExtensions.includes(extension);
};

// 格式化数字
export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

// 计算百分比
export const calculatePercentage = (current: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((current / total) * 100);
};

// 获取状态颜色
export const getStatusColor = (status: string): string => {
  switch (status) {
    case '已完成':
    case '已解析':
    case 'completed':
      return 'text-green-600';
    case '进行中':
    case '上传中':
    case '下载中':
    case '解析中':
    case 'uploading':
    case 'downloading':
    case 'processing':
      return 'text-blue-600';
    case '失败':
    case '错误':
    case '未解析':
    case 'failed':
    case 'error':
      return 'text-red-600';
    case '等待':
    case '待处理':
    case 'waiting':
    case 'pending':
      return 'text-yellow-600';
    case '暂停':
    case 'paused':
      return 'text-gray-600';
    default:
      return 'text-gray-600';
  }
};

// 获取状态图标
export const getStatusIcon = (status: string): string => {
  switch (status) {
    case '已完成':
    case '已解析':
    case 'completed':
      return 'fas fa-check-circle';
    case '进行中':
    case '上传中':
    case '下载中':
    case '解析中':
    case 'uploading':
    case 'downloading':
    case 'processing':
      return 'fas fa-spinner fa-spin';
    case '失败':
    case '错误':
    case '未解析':
    case 'failed':
    case 'error':
      return 'fas fa-exclamation-circle';
    case '等待':
    case '待处理':
    case 'waiting':
    case 'pending':
      return 'fas fa-clock';
    case '暂停':
    case 'paused':
      return 'fas fa-pause-circle';
    default:
      return 'fas fa-question-circle';
  }
};

// 本地存储工具
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // 忽略存储错误
    }
  },
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch {
      // 忽略删除错误
    }
  },
  clear: (): void => {
    try {
      localStorage.clear();
    } catch {
      // 忽略清空错误
    }
  }
};

// 会话存储工具
export const sessionStorage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  set: <T>(key: string, value: T): void => {
    try {
      window.sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // 忽略存储错误
    }
  },
  remove: (key: string): void => {
    try {
      window.sessionStorage.removeItem(key);
    } catch {
      // 忽略删除错误
    }
  },
  clear: (): void => {
    try {
      window.sessionStorage.clear();
    } catch {
      // 忽略清空错误
    }
  }
};

// 错误处理
export const handleError = (error: any, context?: string): void => {
  console.error(`Error${context ? ` in ${context}` : ''}:`, error);
  // 这里可以添加错误上报逻辑
};

// 延迟函数
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// 重试函数
export const retry = async <T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delayMs: number = 1000
): Promise<T> => {
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt < maxAttempts) {
        await delay(delayMs * attempt);
      }
    }
  }
  
  throw lastError;
};