import React from 'react';
import {
  View,
  Text,
  Image,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StatusBar,
} from 'react-native';
import { CyanButton } from '../../components/buttons';

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
            style={fieldStyle}
          />
          <TextInput
            placeholder="Password"
            placeholderTextColor="#440066"
            secureTextEntry
            style={fieldStyle}
          />
          <TextInput
            placeholder="Confirm Password"
            placeholderTextColor="#440066"
            secureTextEntry
            style={fieldStyle}
          />

          <View style={{ marginTop: 16 }}>
            <CyanButton title="Create Account" onPress={() => navigation.navigate('GettingStarted')} />
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
