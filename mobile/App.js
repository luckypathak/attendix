import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, Text, View, TextInput, TouchableOpacity, 
  ActivityIndicator, Alert, SafeAreaView, ScrollView 
} from 'react-native';
import axios from 'axios';

// Services
import GPSService from './services/gps';
import OfflineSyncService from './services/offline_sync';
import SMSGatewayWorker from './services/sms_sender';

const BACKEND_URL = 'http://10.0.2.2:8000/api/v1';

export default function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(null);
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Location states
  const [gpsData, setGpsData] = useState(null);
  const [offlineCount, setOfflineCount] = useState(0);
  const [clockedIn, setClockedIn] = useState(false);

  useEffect(() => {
    // Periodically process background SMS gateway polling (Simulate background worker)
    const smsInterval = setInterval(() => {
      SMSGatewayWorker.executePoll();
    }, 15000);

    // Periodically update offline counts
    const countInterval = setInterval(async () => {
      const size = await OfflineSyncService.getQueueSize();
      setOfflineCount(size);
    }, 5000);

    return () => {
      clearInterval(smsInterval);
      clearInterval(countInterval);
    };
  }, []);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Error', 'Please enter username and password.');
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/auth/login/`, { username, password });
      setToken(res.data.access);
      setUser(res.data.user);
      Alert.alert('Welcome', `Logged in as ${res.data.user.username}`);
    } catch (err) {
      Alert.alert('Login Failed', err.response?.data?.detail || 'Verify your connection credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchGPS = async () => {
    setLoading(true);
    try {
      const data = await GPSService.getCurrentLocation();
      setGpsData(data);
      Alert.alert('GPS Locked', `Accuracy: ${data.accuracy.toFixed(1)}m`);
    } catch (err) {
      Alert.alert('GPS Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClockAction = async (type) => {
    if (!gpsData) {
      Alert.alert('Error', 'Please fetch GPS location first.');
      return;
    }

    const payload = {
      latitude: gpsData.latitude,
      longitude: gpsData.longitude,
      accuracy: gpsData.accuracy,
      address: `Captured on Mobile GPS (Lat ${gpsData.latitude.toFixed(4)})`,
      device_info: 'Android Handset (Attendix Mobile App)'
    };

    setLoading(true);
    try {
      // Try sending online
      await axios.post(`${BACKEND_URL}/attendance/records/${type === 'in' ? 'check-in' : 'check-out'}/`, payload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      setClockedIn(type === 'in');
      setGpsData(null);
      Alert.alert('Success', `Successfully clocked ${type === 'in' ? 'in' : 'out'} online!`);
    } catch (err) {
      // Offline fallback
      console.log('Online request failed, fallback to offline queue.');
      const queued = await OfflineSyncService.queueEvent(
        type === 'in' ? 'check-in' : 'check-out',
        payload,
        token
      );
      if (queued) {
        setClockedIn(type === 'in');
        setGpsData(null);
        Alert.alert('Offline Mode', 'Network is offline. Attendance queued locally.');
      } else {
        Alert.alert('Error', 'Failed to record attendance locally.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForceSync = async () => {
    setLoading(true);
    await OfflineSyncService.syncQueuedEvents();
    const size = await OfflineSyncService.getQueueSize();
    setOfflineCount(size);
    setLoading(false);
    Alert.alert('Sync Finished', `Remaining queued logs: ${size}`);
  };

  if (!token) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.card}>
          <Text style={styles.title}>Attendix OS Mobile</Text>
          <Text style={styles.subtitle}>Workforce OS Handset Portal</Text>
          
          <TextInput 
            style={styles.input} 
            placeholder="Username" 
            placeholderTextColor="#888"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
          <TextInput 
            style={styles.input} 
            placeholder="Password" 
            placeholderTextColor="#888"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />
          
          <TouchableOpacity style={styles.button} onClick={handleLogin} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Log In</Text>}
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.card}>
          <Text style={styles.welcome}>Welcome, {user.username}</Text>
          <Text style={styles.subtitle}>Digital Punch Card</Text>

          <View style={styles.statusBox}>
            <Text style={styles.statusText}>
              Status: <Text style={{ color: clockedIn ? '#00f5d4' : '#ff9f43', fontWeight: 'bold' }}>{clockedIn ? 'Clocked In' : 'Clocked Out'}</Text>
            </Text>
            {gpsData ? (
              <Text style={styles.gpsLock}>GPS: Lat {gpsData.latitude.toFixed(4)}, Lng {gpsData.longitude.toFixed(4)}</Text>
            ) : (
              <Text style={styles.gpsWait}>GPS Coordinates: Pending Fetch</Text>
            )}
          </View>

          <TouchableOpacity style={styles.gpsButton} onClick={handleFetchGPS} disabled={loading}>
            <Text style={styles.buttonText}>Fetch GPS Location</Text>
          </TouchableOpacity>

          <View style={styles.row}>
            <TouchableOpacity 
              style={[styles.halfButton, { opacity: clockedIn ? 0.5 : 1 }]} 
              onClick={() => handleClockAction('in')} 
              disabled={loading || clockedIn}
            >
              <Text style={styles.buttonText}>Clock In</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.halfButton, { opacity: !clockedIn ? 0.5 : 1, backgroundColor: '#9d4edd' }]} 
              onClick={() => handleClockAction('out')} 
              disabled={loading || !clockedIn}
            >
              <Text style={styles.buttonText}>Clock Out</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Offline Queue card */}
        <View style={[styles.card, { marginTop: 20 }]}>
          <Text style={styles.cardTitle}>Offline Sync Queue</Text>
          <Text style={styles.subtitle}>Offline records cached: {offlineCount}</Text>
          
          <TouchableOpacity style={[styles.button, { backgroundColor: '#6c757d', marginTop: 15 }]} onClick={handleForceSync} disabled={loading}>
            <Text style={styles.buttonText}>Sync Queue Now</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0915',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scroll: {
    padding: 20,
    width: '100%',
  },
  card: {
    backgroundColor: '#121124',
    borderRadius: 16,
    padding: 24,
    width: 320,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  welcome: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#adb5bd',
    marginBottom: 24,
  },
  input: {
    width: '100%',
    height: 48,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 8,
    paddingHorizontal: 16,
    color: '#fff',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  button: {
    width: '100%',
    height: 48,
    backgroundColor: '#7b2cbf',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  gpsButton: {
    width: '100%',
    height: 48,
    backgroundColor: '#018786',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  halfButton: {
    flex: 1,
    height: 48,
    backgroundColor: '#00f5d4',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  statusBox: {
    width: '100%',
    padding: 16,
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 8,
    marginBottom: 20,
    alignItems: 'center',
  },
  statusText: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 6,
  },
  gpsLock: {
    color: '#00f5d4',
    fontSize: 13,
  },
  gpsWait: {
    color: '#adb5bd',
    fontSize: 13,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  }
});
