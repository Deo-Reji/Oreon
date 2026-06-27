// Base URL for the backend API.
//
// React Native cannot use "localhost" — that points at the phone/emulator
// itself, not your dev machine. Pick the value that matches how you run:
//
//   - Physical device (Expo Go) on same Wi-Fi:  your machine's LAN IP (below)
//   - Android emulator:                         http://10.0.2.2:8000
//   - iOS simulator:                            http://localhost:8000
//
// Also make sure the backend is started so the phone can reach it:
//   uvicorn main:app --host 0.0.0.0 --port 8000
export const API_BASE_URL = 'http://172.20.10.2:8000';
