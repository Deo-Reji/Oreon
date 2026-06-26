import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import { BottomNav } from '../../components/navigation';
import { CyanButton } from '../../components/buttons';
import { useTabSwipe } from '../../hooks/useTabSwipe';
import { CommonActions } from '@react-navigation/native';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const PLACEHOLDER_BODY =
  '"This section serves as a placeholder for a specific function that will be fully defined and implemented in a later development phase. At Oreon, we believe that your digital workspace should be as intuitive as your own thoughts. By bridging the gap between high-performance utility and seamless user connection, our platform empowers you to orchestrate your daily workflows with unprecedented clarity. Whether you are fine-tuning your personal identity in the global ecosystem or calibrating your deep-work settings for maximum focus, every interaction is designed to be fluid, responsive, and uniquely yours. Welcome to the next evolution of integrated digital living—where your data stays secure, your tools stay connected, and your potential remains limitless."';

export default function AccountSettings({ navigation }) {
  const [activeTab, setActiveTab] = useState('account');
  const panHandlers = useTabSwipe(2, navigation);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }} {...panHandlers}>

        {/* Logo */}
        <View style={{ paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
          <Image source={require('../../../assets/logo.png')} style={{ width: 50, height: 50 }} resizeMode="contain" />
        </View>

        {/* Title */}
        <Text
          style={[
            glowText,
            {
              color: '#FFF',
              fontWeight: '900',
              fontSize: 36,
              textTransform: 'uppercase',
              letterSpacing: 2,
              textAlign: 'center',
              marginBottom: 16,
            },
          ]}
        >
          Account/Settings
        </Text>

        {/* Panel */}
        <View
          style={{
            flex: 1,
            backgroundColor: MAGENTA,
            marginHorizontal: 16,
            borderRadius: 20,
            overflow: 'hidden',
          }}
        >
          {/* Tab Bar */}
          <View style={{ flexDirection: 'row', margin: 12 }}>
            {['account', 'settings'].map(t => (
              <TouchableOpacity
                key={t}
                onPress={() => setActiveTab(t)}
                style={{
                  flex: 1,
                  paddingVertical: 8,
                  borderRadius: 20,
                  backgroundColor: activeTab === t ? CYAN : 'transparent',
                  alignItems: 'center',
                }}
              >
                <Text
                  style={{
                    color: '#FFF',
                    fontWeight: '900',
                    textTransform: 'uppercase',
                    fontSize: 13,
                    letterSpacing: 1,
                  }}
                >
                  {t === 'account' ? 'Account' : 'Settings'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 24 }}>
            <Text style={{ color: '#FFF', fontSize: 14, lineHeight: 22 }}>
              {PLACEHOLDER_BODY}
            </Text>
          </ScrollView>
        </View>

        <View style={{ paddingHorizontal: 16, paddingVertical: 12 }}>
          <CyanButton
            title="Log Out"
            onPress={() =>
              navigation.dispatch(
                CommonActions.reset({ index: 0, routes: [{ name: 'OnboardingSplash' }] })
              )
            }
          />
        </View>
        <BottomNav activeIndex={2} />
      </View>
    </SafeAreaView>
  );
}
