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

export default function SignUp({ navigation }) {
  const { signUp } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSignUp() {
    if (!email || !password) {
      Alert.alert('Missing info', 'Please enter your email and password.');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Passwords do not match', 'Please re-enter your password.');
      return;
    }
    setSubmitting(true);
    try {
      await signUp(email.trim(), password);
      navigation.reset({ index: 0, routes: [{ name: 'GettingStarted' }] });
    } catch (err) {
      Alert.alert('Sign up failed', err.message);
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
            Sign Up
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
          <TextInput
            placeholder="Confirm Password"
            placeholderTextColor="#440066"
            secureTextEntry
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            style={fieldStyle}
          />

          <View style={{ marginTop: 16 }}>
            <CyanButton
              title={submitting ? 'Creating...' : 'Create Account'}
              onPress={handleSignUp}
              disabled={submitting}
            />
          </View>

          <TouchableOpacity
            style={{ marginTop: 20, alignItems: 'center' }}
            onPress={() => navigation.navigate('SignIn')}
          >
            <Text style={{ color: '#FFF', fontWeight: '700', fontSize: 14 }}>Sign In</Text>
          </TouchableOpacity>

        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
