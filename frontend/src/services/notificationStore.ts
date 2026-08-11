/**
 * Notification Store & Management Service for Cortex NIDS.
 * Connects to live alerts and provides unread counters, notification history,
 * mark-as-read, and drawer toggle actions.
 */
import { apiService, getWebSocketUrl } from './api';

export interface SOCNotification {
  id: string;
  timestamp: string;
  title: string;
  message: string;
  attack_type: string;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  risk_score: number;
  read: boolean;
  src_ip?: string;
  dst_port?: number;
}

type NotificationListener = (notifications: SOCNotification[]) => void;

class NotificationStore {
  private notifications: SOCNotification[] = [];
  private listeners: Set<NotificationListener> = new Set();
  private ws: WebSocket | null = null;

  constructor() {
    this.initFromStorage();
    this.initWebSocket();
    this.fetchRecentCriticalAlerts();
  }

  private initFromStorage() {
    try {
      const stored = localStorage.getItem('cortex_notifications');
      if (stored) {
        this.notifications = JSON.parse(stored);
      }
    } catch {
      this.notifications = [];
    }
  }

  private saveToStorage() {
    try {
      localStorage.setItem('cortex_notifications', JSON.stringify(this.notifications.slice(0, 50)));
    } catch {
      // Ignore storage errors
    }
  }

  private initWebSocket() {
    try {
      const wsUrl = getWebSocketUrl();
      this.ws = new WebSocket(wsUrl);

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const riskLevel = data.risk_level || 'Low';
          
          // Only create notification for High and Critical alerts
          if (riskLevel === 'Critical' || riskLevel === 'High') {
            const notif: SOCNotification = {
              id: data.id || `NOTIF-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
              timestamp: data.timestamp || new Date().toLocaleTimeString(),
              title: `🚨 ${data.attack_type || 'Security Risk'} Detected`,
              message: `High risk flow from ${data.src_ip || 'unknown IP'} on port ${data.dst_port || 80}`,
              attack_type: data.attack_type || 'Attack',
              risk_level: riskLevel,
              risk_score: typeof data.risk_score === 'number' ? data.risk_score : 80.0,
              read: false,
              src_ip: data.src_ip,
              dst_port: data.dst_port,
            };
            this.addNotification(notif);
          }
        } catch {
          // Ignore parse errors
        }
      };
    } catch {
      // WebSocket setup error
    }
  }

  public async fetchRecentCriticalAlerts() {
    try {
      const res = await apiService.getHistoricalThreats({
        page: 1,
        page_size: 10,
        risk_level: 'Critical',
      });
      if (res && Array.isArray(res.alerts)) {
        res.alerts.forEach((alt: any) => {
          const id = `DB-${alt.id}`;
          if (!this.notifications.some((n) => n.id === id)) {
            this.notifications.push({
              id,
              timestamp: alt.timestamp,
              title: `🚨 Critical Alert: ${alt.attack_type}`,
              message: `Recorded critical attack from ${alt.src_ip || '192.168.1.1'}`,
              attack_type: alt.attack_type,
              risk_level: alt.risk_level || 'Critical',
              risk_score: alt.risk_score || 85.0,
              read: false,
              src_ip: alt.src_ip,
              dst_port: alt.dst_port,
            });
          }
        });
        this.notifyListeners();
      }
    } catch {
      // Ignore fetch errors
    }
  }

  public addNotification(notif: SOCNotification) {
    if (!this.notifications.some((n) => n.id === notif.id)) {
      this.notifications = [notif, ...this.notifications.slice(0, 49)];
      this.saveToStorage();
      this.notifyListeners();
    }
  }

  public markAllAsRead() {
    this.notifications = this.notifications.map((n) => ({ ...n, read: true }));
    this.saveToStorage();
    this.notifyListeners();
  }

  public markAsRead(id: string) {
    this.notifications = this.notifications.map((n) => (n.id === id ? { ...n, read: true } : n));
    this.saveToStorage();
    this.notifyListeners();
  }

  public clearAll() {
    this.notifications = [];
    this.saveToStorage();
    this.notifyListeners();
  }

  public getNotifications(): SOCNotification[] {
    return this.notifications;
  }

  public getUnreadCount(): number {
    return this.notifications.filter((n) => !n.read).length;
  }

  public subscribe(listener: NotificationListener): () => void {
    this.listeners.add(listener);
    listener(this.notifications);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach((l) => l(this.notifications));
  }
}

export const notificationStore = new NotificationStore();
