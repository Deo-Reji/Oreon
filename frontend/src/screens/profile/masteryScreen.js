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
import { useTabSwipe } from '../../hooks/useTabSwipe';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const BADGE_DATA = [
  { exercise: 'Hammer\nCurl', stars: 2 },
  { exercise: 'Lat\nRaise', stars: 1 },
  { exercise: 'Bench\nPress', stars: 3 },
  { exercise: 'Hip\nAbductors', stars: 1 },
  { exercise: 'Leg\nPress', stars: 3 },
];

const StarBadge = ({ size = 36 }) => (
  <Text style={{ fontSize: size, lineHeight: size + 4 }}>⭐</Text>
);

export default function MasteryScreen({ navigation }) {
  const [activeTab, setActiveTab] = useState('badges');
  const panHandlers = useTabSwipe(0, navigation);

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
              fontSize: 44,
              textTransform: 'uppercase',
              letterSpacing: 3,
              textAlign: 'center',
              marginBottom: 16,
            },
          ]}
        >
          Mastery
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
            {['badges', 'leaderboard'].map(t => (
              <TouchableOpacity
                key={t}
                onPress={() =>
                  t === 'leaderboard'
                    ? navigation.navigate('LeaderboardScreen')
                    : setActiveTab(t)
                }
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
                  {t === 'badges' ? 'Badges' : 'Leaderboard'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 24 }}>
            {BADGE_DATA.map(({ exercise, stars }) => (
              <View key={exercise} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24 }}>
                <Text
                  style={{
                    color: '#FFF',
                    fontWeight: '900',
                    fontSize: 14,
                    textTransform: 'uppercase',
                    width: 90,
                    letterSpacing: 0.5,
                  }}
                >
                  {exercise}
                </Text>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  {Array.from({ length: stars }).map((_, i) => (
                    <StarBadge key={i} size={32} />
                  ))}
                </View>
              </View>
            ))}
          </ScrollView>
        </View>

        <View style={{ height: 12 }} />
        <BottomNav activeIndex={0} />
      </View>
    </SafeAreaView>
  );
}
