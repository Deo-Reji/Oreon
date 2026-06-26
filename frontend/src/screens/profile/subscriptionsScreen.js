import React from 'react';
import {
  View,
  Text,
  Image,
  SafeAreaView,
  ScrollView,
  Alert,
  StatusBar,
} from 'react-native';
import { BottomNav } from '../../components/navigation';
import { YellowButton } from '../../components/buttons';
import { useTabSwipe } from '../../hooks/useTabSwipe';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const PLACEHOLDER_BODY =
  '"This section serves as a placeholder for a specific function that will be fully defined and implemented in a later development phase. At Oreon, we believe that your digital workspace should be as intuitive as your own thoughts. By bridging the gap between high-performance utility and seamless user connection, our platform empowers you to orchestrate your daily workflows with unprecedented clarity. Whether you are fine-tuning your personal identity in the global ecosystem or calibrating your deep-work settings for maximum focus, every interaction is designed to be fluid, responsive, and uniquely yours. Welcome to the next evolution of integrated digital living—where your data stays secure, your tools stay connected, and your potential remains limitless."';

export default function SubscriptionsScreen({ navigation }) {
  const panHandlers = useTabSwipe(3, navigation);
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
              fontSize: 38,
              textTransform: 'uppercase',
              letterSpacing: 2,
              textAlign: 'center',
              marginBottom: 16,
            },
          ]}
        >
          Subscriptons
        </Text>

        <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 20 }}>
          {/* PRO Card */}
          <View
            style={{
              backgroundColor: MAGENTA,
              borderRadius: 18,
              padding: 20,
              marginBottom: 20,
            }}
          >
            <Text
              style={{
                color: '#FFF',
                fontWeight: '900',
                fontSize: 22,
                textTransform: 'uppercase',
                letterSpacing: 1,
                marginBottom: 10,
              }}
            >
              Pro (Suggested)
            </Text>
            <Text style={{ color: '#FFF', fontSize: 13, lineHeight: 20, marginBottom: 16 }}>
              {PLACEHOLDER_BODY}
            </Text>
            <YellowButton
              title="Buy Now"
              onPress={() => Alert.alert('Subscribe', 'Open Pro subscription purchase flow')}
            />
          </View>

          {/* FREE Card */}
          <View
            style={{
              backgroundColor: CYAN,
              borderRadius: 18,
              padding: 20,
            }}
          >
            <Text
              style={{
                color: '#FFF',
                fontWeight: '900',
                fontSize: 22,
                textTransform: 'uppercase',
                letterSpacing: 1,
                marginBottom: 10,
              }}
            >
              Free (Current)
            </Text>
            <Text style={{ color: '#FFF', fontSize: 13, lineHeight: 20 }}>
              {PLACEHOLDER_BODY}
            </Text>
          </View>
        </ScrollView>

        <BottomNav activeIndex={3} />
      </View>
    </SafeAreaView>
  );
}
