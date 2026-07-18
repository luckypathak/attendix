import { useEffect, useRef } from 'react';
import api from '../services/api';

export default function useBackgroundLocation(isCheckedIn, workCategory, companySettings) {
  const intervalRef = useRef(null);
  
  useEffect(() => {
    if (!isCheckedIn) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }
    
    // Default to 5 mins if not set
    const updateFrequencyMins = companySettings?.location_update_frequency_minutes || 5;
    
    // For battery optimization, don't ping every second.
    // Office staff gets pinged every configured minutes (e.g. 2-5 mins)
    // Field staff gets pinged every configured minutes (e.g. 5 mins)
    
    const sendPing = () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
          try {
            await api.post('/attendance/ping/', {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              speed: position.coords.speed
            });
          } catch (e) {
            console.error('Location ping failed', e);
          }
        }, (error) => {
          console.error('Error getting location', error);
        }, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        });
      }
    };
    
    // Initial ping
    sendPing();
    
    intervalRef.current = setInterval(() => {
      sendPing();
    }, updateFrequencyMins * 60 * 1000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isCheckedIn, workCategory, companySettings]);
}
