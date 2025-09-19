/**
 * WebSocket服务
 * 
 * 提供WebSocket连接管理和实时消息处理功能
 */

import { API_BASE_URL } from '../config';

// WebSocket消息类型
export interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
  timestamp?: string;
  task_id?: string;
  error?: string;
}

// 任务更新数据
export interface TaskUpdateData {
  task_id: string;
  status: string;
  progress: number;
  title: string;
  platform: string;
  updated_at: string;
  error_message?: string;
  file_path?: string;
}

// 下载完成数据
export interface DownloadCompleteData {
  task_id: string;
  title: string;
  platform: string;
  file_path: string;
  completed_at: string;
}

// 下载失败数据
export interface DownloadFailedData {
  task_id: string;
  title: string;
  platform: string;
  error_message: string;
  failed_at: string;
}

// 事件监听器类型
type EventListener = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private eventListeners: Map<string, EventListener[]> = new Map();
  private isConnecting = false;
  private shouldReconnect = true;
  
  /**
   * 连接WebSocket
   */
  connect(userId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // 如果已经连接，直接返回
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      
      // 如果正在连接，等待当前连接完成
      if (this.isConnecting) {
        // 等待一段时间后重试
        setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            resolve();
          } else {
            reject(new Error('WebSocket连接超时'));
          }
        }, 3000);
        return;
      }
      
      // 清理现有连接
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      this.isConnecting = true;
      
      // 构建WebSocket URL
      const wsUrl = API_BASE_URL.replace('http', 'ws') + `/websocket/ws/${userId}`;
      
      try {
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          console.log('WebSocket连接已建立');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('connected', { userId });
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };
        
        this.ws.onclose = (event) => {
          console.log('WebSocket连接已关闭:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(userId);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error);
          this.isConnecting = false;
          this.emit('error', { error });
          reject(error);
        };
        
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }
  
  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, '主动断开连接');
      this.ws = null;
    }
  }
  
  /**
   * 发送消息
   */
  send(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }
    
    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      return false;
    }
  }
  
  /**
   * 订阅任务更新
   */
  subscribeTask(taskId: string): boolean {
    return this.send({
      type: 'subscribe_task',
      task_id: taskId
    });
  }
  
  /**
   * 取消订阅任务更新
   */
  unsubscribeTask(taskId: string): boolean {
    return this.send({
      type: 'unsubscribe_task',
      task_id: taskId
    });
  }
  
  /**
   * 发送心跳
   */
  ping(): boolean {
    return this.send({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  }
  
  /**
   * 获取连接统计
   */
  getStats(): boolean {
    return this.send({
      type: 'get_stats'
    });
  }
  
  /**
   * 添加事件监听器
   */
  on(event: string, listener: EventListener): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(listener);
  }
  
  /**
   * 移除事件监听器
   */
  off(event: string, listener: EventListener): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * 触发事件
   */
  private emit(event: string, data: any): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`事件监听器执行失败 (${event}):`, error);
        }
      });
    }
  }
  
  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('收到WebSocket消息:', message);
    
    switch (message.type) {
      case 'connection_established':
        this.emit('connection_established', message);
        break;
        
      case 'task_update':
        this.emit('task_update', message.data as TaskUpdateData);
        break;
        
      case 'download_complete':
        this.emit('download_complete', message.data as DownloadCompleteData);
        break;
        
      case 'download_failed':
        this.emit('download_failed', message.data as DownloadFailedData);
        break;
        
      case 'subscription_confirmed':
        this.emit('subscription_confirmed', message);
        break;
        
      case 'unsubscription_confirmed':
        this.emit('unsubscription_confirmed', message);
        break;
        
      case 'pong':
        this.emit('pong', message);
        break;
        
      case 'stats':
        this.emit('stats', message.data);
        break;
        
      case 'broadcast':
        this.emit('broadcast', message.data);
        break;
        
      case 'error':
        this.emit('message_error', message);
        break;
        
      default:
        console.warn('未知的WebSocket消息类型:', message.type);
        this.emit('unknown_message', message);
    }
  }
  
  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.ping();
    }, 30000); // 每30秒发送一次心跳
  }
  
  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  /**
   * 安排重连
   */
  private scheduleReconnect(userId: string): void {
    this.reconnectAttempts++;
    console.log(`安排WebSocket重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect(userId).catch(error => {
          console.error('WebSocket重连失败:', error);
        });
      }
    }, this.reconnectInterval * this.reconnectAttempts);
  }
  
  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  
  /**
   * 获取连接状态文本
   */
  get connectionState(): string {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }
}

// 创建并导出WebSocket服务实例
export const websocketService = new WebSocketService();
export default websocketService;