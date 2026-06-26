import React from 'react';
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

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const TIPS = [
  'Flared Elbows',
  'Biceps Activation',
  'Grip',
  'Bar Placement',
];

export default function ExerciseDetail({ navigation, route }) {
  const { exerciseName = 'Bench Press', tips = TIPS } = route?.params ?? {};
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }}>

        {/* Logo */}
        <View style={{ paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
          <Image source={require('../../../assets/logo.png')} style={{ width: 50, height: 50 }} resizeMode="contain" />
        </View>

        {/* Back + Title */}
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, marginBottom: 16 }}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginRight: 12 }}>
            <Text style={[glowText, { color: '#FFF', fontSize: 32, fontWeight: '700' }]}>‹</Text>
          </TouchableOpacity>
          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '900',
                fontSize: 34,
                textTransform: 'uppercase',
                letterSpacing: 2,
                flexShrink: 1,
              },
            ]}
          >
            {exerciseName}
          </Text>
        </View>

        <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 20 }}>
          {/* Video Player Placeholder */}
          <View
            style={{
              backgroundColor: '#87CEEB',
              borderRadius: 10,
              height: 200,
              marginBottom: 24,
              overflow: 'hidden',
              justifyContent: 'flex-end',
            }}
          >
            <View style={{ backgroundColor: '#4CAF50', height: 60 }} />
            <View
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                backgroundColor: 'rgba(0,0,0,0.6)',
                flexDirection: 'row',
                alignItems: 'center',
                paddingHorizontal: 8,
                paddingVertical: 6,
                gap: 6,
              }}
            >
              <Text style={{ color: '#FFF', fontSize: 12 }}>▶  ⏸  ◼</Text>
              <View
                style={{
                  flex: 1,
                  height: 3,
                  backgroundColor: '#555',
                  borderRadius: 2,
                  marginHorizontal: 4,
                }}
              >
                <View
                  style={{
                    width: '30%',
                    height: '100%',
                    backgroundColor: '#FF0000',
                    borderRadius: 2,
                  }}
                />
              </View>
              <Text style={{ color: '#FFF', fontSize: 12 }}>🔊  ⛶</Text>
            </View>
          </View>

          {/* Tips */}
          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '900',
                fontSize: 22,
                textTransform: 'uppercase',
                letterSpacing: 1,
                marginBottom: 14,
              },
            ]}
          >
            Things to Look Out For:
          </Text>
          {tips.map(tip => (
            <View key={tip} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
              <Text style={[glowText, { color: '#FFF', fontSize: 18, marginRight: 10, fontWeight: '900' }]}>
                •
              </Text>
              <Text
                style={[
                  glowText,
                  {
                    color: '#FFF',
                    fontWeight: '800',
                    fontSize: 20,
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  },
                ]}
              >
                {tip}
              </Text>
            </View>
          ))}

          {/* CTA */}
          <View style={{ marginTop: 24 }}>
            <CyanButton
              title="Test Your Form!"
              onPress={() => navigation.navigate('WorkoutSession', { exerciseName })}
            />
          </View>
        </ScrollView>

        <BottomNav activeIndex={1} />
      </View>
    </SafeAreaView>
  );
}
