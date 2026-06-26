import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

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

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="OnboardingSplash"
        screenOptions={{ headerShown: false, animation: 'fade', gestureEnabled: false }}
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
  );
}
