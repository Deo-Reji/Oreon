import React from 'react';
import { View, Text, Image, SafeAreaView, StatusBar } from 'react-native';
import { CyanButton, MagentaButton } from '../../components/buttons';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

export default function OnboardingSplash({ navigation }) {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingHorizontal: 32,
          paddingVertical: 40,
        }}
      >
        {/* Logo */}
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <Image source={require('../../../assets/logo.png')} style={{ width: 240, height: 240 }} resizeMode="contain" />
        </View>

        {/* Heading */}
        <View style={{ alignItems: 'center', marginBottom: 30 }}>
          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '900',
                fontSize: 52,
                textTransform: 'uppercase',
                textAlign: 'center',
                letterSpacing: 2,
                lineHeight: 58,
              },
            ]}
          >
            Welcome to{'\n'}Oreon!
          </Text>
        </View>

        {/* Tagline */}
        <View style={{ alignItems: 'center', marginBottom: 40 }}>
          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '800',
                fontSize: 22,
                textTransform: 'uppercase',
                letterSpacing: 3,
              },
            ]}
          >
            Elavate Yourself.
          </Text>
        </View>

        {/* Buttons */}
        <View style={{ flexDirection: 'row', gap: 16, width: '100%' }}>
          <CyanButton
            title="Sign In"
            onPress={() => navigation.navigate('SignIn')}
            style={{ flex: 1 }}
          />
          <MagentaButton
            title="Sign Up"
            onPress={() => navigation.navigate('SignUp')}
            style={{ flex: 1 }}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}
