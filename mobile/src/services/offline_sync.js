import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const QUEUE_KEY = '@attendix_attendance_queue';
const BACKEND_URL = 'http://10.0.2.2:8000/api/v1'; // Standard Android Emulator host mapping for localhost

export class OfflineSyncService {
  /**
   * Queue a check-in or check-out event locally when offline.
   */
  static async queueEvent(type, payload, token) {
    try {
      const existingQueueStr = await AsyncStorage.getItem(QUEUE_KEY);
      const queue = existingQueueStr ? JSON.parse(existingQueueStr) : [];
      
      queue.push({
        type, // 'check-in' or 'check-out'
        payload,
        token,
        timestamp: new Date().toISOString()
      });

      await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
      console.log(`Offline: queued ${type} action locally.`);
      return true;
    } catch (e) {
      console.error('Failed to queue offline event:', e);
      return false;
    }
  }

  /**
   * Sync queued events to the Django server when connectivity is restored.
   */
  static async syncQueuedEvents() {
    try {
      const queueStr = await AsyncStorage.getItem(QUEUE_KEY);
      if (!queueStr) return;

      const queue = JSON.parse(queueStr);
      if (queue.length === 0) return;

      console.log(`Sync worker: attempting to upload ${queue.length} events...`);
      const failedEvents = [];

      for (const item of queue) {
        const url = `${BACKEND_URL}/attendance/records/${item.type}/`;
        
        try {
          await axios.post(url, item.payload, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${item.token}`
            }
          });
          console.log(`Sync worker: successfully synchronized ${item.type} record.`);
        } catch (error) {
          console.error(`Sync worker: failed to upload ${item.type} record:`, error.message);
          // Keep in queue for next retry
          failedEvents.push(item);
        }
      }

      // Update local storage with remaining failed events
      await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(failedEvents));
    } catch (e) {
      console.error('Sync execution failure:', e);
    }
  }

  static async getQueueSize() {
    try {
      const queueStr = await AsyncStorage.getItem(QUEUE_KEY);
      if (!queueStr) return 0;
      return JSON.parse(queueStr).length;
    } catch {
      return 0;
    }
  }
}

export default OfflineSyncService;
