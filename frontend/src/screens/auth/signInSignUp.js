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
import { CyanButton, MagentaButton } from '../../components/buttons';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const inputStyle = {
  backgroundColor: MAGENTA,
  borderRadius: 25,
  paddingVertical: 14,
  paddingHorizontal: 18,
  color: '#FFF',
  fontWeight: '700',
  fontSize: 15,
  marginBottom: 14,
};

export default function SignInSignUp({ navigation }) {
  const [tab, setTab] = useState('signin');

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} keyboardShouldPersistTaps="handled">
        <View style={{ flex: 1, paddingHorizontal: 24, paddingTop: 32, paddingBottom: 40 }}>

          {/* Small Logo */}
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 28,
              backgroundColor: '#1A0033',
              borderWidth: 2,
              borderColor: MAGENTA,
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 24,
            }}
          >
            <Image source={require('../../../assets/logo.png')} style={{ width: 50, height: 50 }} resizeMode="contain" />
          </View>

          {/* Title */}
          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '900',
                fontSize: 40,
                textTransform: 'uppercase',
                letterSpacing: 2,
                marginBottom: 28,
              },
            ]}
          >
            {tab === 'signin' ? 'Sign In' : 'Sign Up'}
          </Text>

          {/* Tab Toggle */}
          <View
            style={{
              flexDirection: 'row',
              marginBottom: 32,
              backgroundColor: MAGENTA,
              borderRadius: 30,
              padding: 4,
            }}
          >
            {['signin', 'signup'].map(t => (
              <TouchableOpacity
                key={t}
                onPress={() => setTab(t)}
                style={{
                  flex: 1,
                  paddingVertical: 10,
                  borderRadius: 26,
                  backgroundColor: tab === t ? CYAN : 'transparent',
                  alignItems: 'center',
                }}
              >
                <Text
                  style={{
                    color: tab === t ? '#000' : '#FFF',
                    fontWeight: '900',
                    textTransform: 'uppercase',
                    fontSize: 14,
                    letterSpacing: 1,
                  }}
                >
                  {t === 'signin' ? 'Sign In' : 'Sign Up'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Form */}
          <TextInput
            placeholder="Email"
            placeholderTextColor="#AA00DD"
            keyboardType="email-address"
            autoCapitalize="none"
            style={inputStyle}
          />
          <TextInput
            placeholder="Password"
            placeholderTextColor="#AA00DD"
            secureTextEntry
            style={inputStyle}
          />
          {tab === 'signup' && (
            <TextInput
              placeholder="Confirm Password"
              placeholderTextColor="#AA00DD"
              secureTextEntry
              style={inputStyle}
            />
          )}

          <View style={{ marginTop: 16 }}>
            {tab === 'signin' ? (
              <CyanButton
                title="Sign In"
                onPress={() => navigation.navigate('HomeScreen')}
              />
            ) : (
              <MagentaButton
                title="Create Account"
                onPress={() => navigation.navigate('GettingStarted')}
              />
            )}
          </View>

          {tab === 'signin' && (
            <TouchableOpacity
              style={{ marginTop: 20, alignItems: 'center' }}
              onPress={() => Alert.alert('Forgot Password', 'Password reset flow')}
            >
              <Text style={{ color: CYAN, fontWeight: '700', fontSize: 14 }}>
                Forgot Password?
              </Text>
            </TouchableOpacity>
          )}

        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
