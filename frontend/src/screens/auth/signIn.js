import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  StatusBar,
} from 'react-native';
import { CyanButton } from '../../components/buttons';
import { useAuth } from '../../hooks/useAuth';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const fieldStyle = {
  backgroundColor: MAGENTA,
  borderRadius: 25,
  paddingVertical: 14,
  paddingHorizontal: 18,
  color: '#FFF',
  fontWeight: '700',
  fontSize: 15,
  marginBottom: 14,
};

export default function SignIn({ navigation }) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSignIn() {
    if (!email || !password) {
      Alert.alert('Missing info', 'Please enter your email and password.');
      return;
    }
    setSubmitting(true);
    try {
      await signIn(email.trim(), password);
      navigation.reset({ index: 0, routes: [{ name: 'HomeScreen' }] });
    } catch (err) {
      Alert.alert('Sign in failed', err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} keyboardShouldPersistTaps="handled">
        <View style={{ flex: 1, paddingHorizontal: 24, paddingTop: 32, paddingBottom: 40 }}>

          <Image
            source={require('../../../assets/logo.png')}
            style={{ width: 56, height: 56, marginBottom: 24 }}
            resizeMode="contain"
          />

          <Text style={[glowText, { color: '#FFF', fontWeight: '900', fontSize: 40, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 28 }]}>
            Sign In
          </Text>

          <TextInput
            placeholder="Email"
            placeholderTextColor="#440066"
            keyboardType="email-address"
            autoCapitalize="none"
            value={email}
            onChangeText={setEmail}
            style={fieldStyle}
          />
          <TextInput
            placeholder="Password"
            placeholderTextColor="#440066"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            style={fieldStyle}
          />

          <View style={{ marginTop: 16 }}>
            <CyanButton
              title={submitting ? 'Signing In...' : 'Sign In'}
              onPress={handleSignIn}
              disabled={submitting}
            />
          </View>

          <TouchableOpacity
            style={{ marginTop: 20, alignItems: 'center' }}
            onPress={() => Alert.alert('Forgot Password', 'Password reset flow')}
          >
            <Text style={{ color: '#FFF', fontWeight: '700', fontSize: 14 }}>Forgot Password?</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={{ marginTop: 14, alignItems: 'center' }}
            onPress={() => navigation.navigate('SignUp')}
          >
            <Text style={{ color: '#FFF', fontWeight: '700', fontSize: 14 }}>Sign Up</Text>
          </TouchableOpacity>

        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
