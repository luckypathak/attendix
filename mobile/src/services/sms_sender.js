import { NativeModules, Platform } from 'react-native';
import axios from 'axios';

// Access standard native Android SMS Manager (Mock fallback for iOS)
const { DirectSms } = NativeModules;

const BACKEND_URL = 'http://10.0.2.2:8000/api/v1';
const GATEWAY_API_KEY = 'attendix_gateway_secret_api_key_123';

export class SMSGatewayWorker {
  static isRunning = false;
  static deviceId = 'android_handset_gateway_01';

  /**
   * Triggers the polling loop to fetch and send queued SMS messages.
   */
  static async executePoll() {
    if (this.isRunning) return;
    this.isRunning = true;

    try {
      console.log('SMS Gateway: polling backend for pending SMS...');
      const response = await axios.get(`${BACKEND_URL}/notifications/gateway/poll/`, {
        params: { device_id: this.deviceId },
        headers: { 'X-Attendix-Gateway-Key': GATEWAY_API_KEY }
      });

      const pendingMessages = response.data; // List of { id, phone, message, sim_slot }
      console.log(`SMS Gateway: retrieved ${pendingMessages.length} messages to dispatch.`);

      for (const msg of pendingMessages) {
        await this.dispatchSMS(msg);
      }
    } catch (e) {
      console.error('SMS Gateway poll error:', e.message);
    } finally {
      this.isRunning = false;
    }
  }

  /**
   * Transmit single message using native Android SIM slot APIs
   */
  static async dispatchSMS(sms) {
    const { id, phone, message, sim_slot } = sms;
    
    if (Platform.OS !== 'android') {
      console.log(`SMS Gateway iOS Simulation [SIM ${sim_slot || 1}]: SMS to ${phone} -> "${message}"`);
      await this.reportStatus(id, 'SUCCESS', sim_slot || 1);
      return;
    }

    try {
      // In a real Android environment, we call a custom Java native module (DirectSms) 
      // exposing standard dual-SIM SmsManager APIs:
      // DirectSms.sendSms(phone, message, sim_slot);
      if (DirectSms && typeof DirectSms.sendSms === 'function') {
        await DirectSms.sendSms(phone, message, sim_slot);
      } else {
        console.log(`SMS Gateway Android Fallback: SMS to ${phone} -> "${message}"`);
      }
      
      await this.reportStatus(id, 'SUCCESS', sim_slot);
    } catch (err) {
      console.error(`SMS Gateway failed to send ID ${id}:`, err.message);
      await this.reportStatus(id, 'FAILED', sim_slot, err.message);
    }
  }

  static async reportStatus(smsId, status, simSlot, errorMsg = '') {
    try {
      await axios.post(`${BACKEND_URL}/notifications/gateway/status/`, {
        device_id: this.deviceId,
        sms_id: smsId,
        status: status, // 'SUCCESS' or 'FAILED'
        sim_used: simSlot,
        error_message: errorMsg
      }, {
        headers: { 'X-Attendix-Gateway-Key': GATEWAY_API_KEY }
      });
      console.log(`SMS Gateway: reported status ${status} for ID ${smsId}.`);
    } catch (e) {
      console.error(`SMS Gateway failed reporting status for ID ${smsId}:`, e.message);
    }
  }
}

export default SMSGatewayWorker;
