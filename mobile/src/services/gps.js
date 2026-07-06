import { Platform } from 'react-native';
import Geolocation from 'react-native-geolocation-service';
import { check, request, PERMISSIONS, RESULTS } from 'react-native-permissions';

export class GPSService {
  static async requestLocationPermission() {
    const permission = Platform.select({
      android: PERMISSIONS.ANDROID.ACCESS_FINE_LOCATION,
      ios: PERMISSIONS.IOS.LOCATION_WHEN_IN_USE,
    });

    try {
      const status = await check(permission);
      if (status === RESULTS.GRANTED) {
        return true;
      }
      
      const requestStatus = await request(permission);
      return requestStatus === RESULTS.GRANTED;
    } catch (error) {
      console.error('Error requesting location permission:', error);
      return false;
    }
  }

  static getCurrentLocation() {
    return new Promise(async (resolve, reject) => {
      const hasPermission = await this.requestLocationPermission();
      if (!hasPermission) {
        return reject(new Error('Location services permission denied. Access is required for clock-in/out.'));
      }

      Geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy, timestamp } = position.coords;
          
          // Require high-accuracy GPS (less than 50 meters)
          if (accuracy > 50) {
            return reject(new Error(`GPS accuracy is low (${accuracy.toFixed(1)}m). Move to an open area and retry.`));
          }

          resolve({
            latitude,
            longitude,
            accuracy,
            timestamp: new Date(timestamp).toISOString(),
          });
        },
        (error) => {
          let errorMsg = 'Failed to retrieve location.';
          if (error.code === 1) {
            errorMsg = 'Location permission denied by user.';
          } else if (error.code === 2) {
            errorMsg = 'GPS/High Accuracy services are turned OFF. Please turn location ON.';
          } else if (error.code === 3) {
            errorMsg = 'GPS location retrieval timed out.';
          }
          reject(new Error(errorMsg));
        },
        { 
          enableHighAccuracy: true, 
          timeout: 15000, 
          maximumAge: 0 // Do not use cached locations
        }
      );
    });
  }
}
export default GPSService;
