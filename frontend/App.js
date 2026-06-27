import { useEffect } from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as ScreenOrientation from 'expo-screen-orientation';

import { AuthProvider } from './src/state/authContext';
import OnboardingSplash from './src/screens/auth/onBoardingSplash';
import SignIn from './src/screens/auth/signIn';
import SignUp from './src/screens/auth/signUp';
import GettingStarted from './src/screens/auth/gettingStarted';
import HomeScreen from './src/screens/home/homeScreen';
import ExerciseList from './src/screens/home/exerciseList';
import ExerciseDetail from './src/screens/workout/exerciseDetail';
import WorkoutSession from './src/screens/workout/workoutSession';
import FormResults from './src/screens/results/formResults';
import MasteryScreen from './src/screens/profile/masteryScreen';
import LeaderboardScreen from './src/screens/profile/leaderboardScreen';
import AccountSettings from './src/screens/profile/accountSettings';
import SubscriptionsScreen from './src/screens/profile/subscriptionsScreen';

const Stack = createNativeStackNavigator();

// Black root background so rotation/transitions never flash white.
const AppTheme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: '#000' },
};

export default function App() {
  // Lock the app to portrait by default; the workout screen unlocks itself
  // so it can rotate to landscape for wide-angle recording.
  useEffect(() => {
    ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP);
  }, []);

  return (
    <SafeAreaProvider>
      <AuthProvider>
      <NavigationContainer theme={AppTheme}>
        <Stack.Navigator
          initialRouteName="OnboardingSplash"
          screenOptions={{
            headerShown: false,
            animation: 'fade',
            gestureEnabled: false,
            contentStyle: { backgroundColor: '#000' },
          }}
        >
          <Stack.Screen name="OnboardingSplash" component={OnboardingSplash} />
        <Stack.Screen name="SignIn" component={SignIn} />
        <Stack.Screen name="SignUp" component={SignUp} />
        <Stack.Screen name="GettingStarted" component={GettingStarted} />
        <Stack.Screen name="HomeScreen" component={HomeScreen} />
        <Stack.Screen name="ExerciseList" component={ExerciseList} />
        <Stack.Screen name="ExerciseDetail" component={ExerciseDetail} />
        <Stack.Screen name="WorkoutSession" component={WorkoutSession} />
        <Stack.Screen name="FormResults" component={FormResults} />
        <Stack.Screen name="MasteryScreen" component={MasteryScreen} />
        <Stack.Screen name="LeaderboardScreen" component={LeaderboardScreen} />
        <Stack.Screen name="AccountSettings" component={AccountSettings} />
        <Stack.Screen name="SubscriptionsScreen" component={SubscriptionsScreen} />
        </Stack.Navigator>
      </NavigationContainer>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
