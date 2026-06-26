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

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';
const YELLOW = '#FFD700';
const TEAL = '#00B8CC';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const FILTERS = ['Global', 'Region', 'State', 'Gym'];

const MOCK_DATA = [
  { name: 'John', rank: 1, weight: 225 },
  { name: 'Dereck', rank: 2, weight: 220 },
];

export default function LeaderboardScreen({ navigation }) {
  const [activeFilter, setActiveFilter] = useState('Gym');

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }}>

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
                onPress={() => t === 'badges' ? navigation.navigate('MasteryScreen') : null}
                style={{
                  flex: 1,
                  paddingVertical: 8,
                  borderRadius: 20,
                  backgroundColor: t === 'leaderboard' ? CYAN : 'transparent',
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

          <ScrollView contentContainerStyle={{ paddingHorizontal: 14, paddingBottom: 24 }}>
            {/* Filter buttons */}
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
              {FILTERS.map(f => (
                <TouchableOpacity
                  key={f}
                  onPress={() => setActiveFilter(f)}
                  style={{
                    backgroundColor: activeFilter === f ? YELLOW : TEAL,
                    borderRadius: 20,
                    paddingVertical: 10,
                    paddingHorizontal: 14,
                  }}
                >
                  <Text style={{ color: '#FFF', fontWeight: '700', fontSize: 14 }}>
                    {f}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Note */}
            <Text style={{ color: '#FFF', fontSize: 12, fontStyle: 'italic', marginBottom: 12 }}>
              *To be ranked you have to score a 9.5 or higher on the form
            </Text>

            {/* Table Header */}
            <View
              style={{
                flexDirection: 'row',
                paddingVertical: 8,
                marginBottom: 4,
                borderBottomWidth: 1,
                borderBottomColor: '#FFF',
              }}
            >
              {['Name', 'Rank', 'Weight'].map(h => (
                <Text
                  key={h}
                  style={{
                    flex: 1,
                    color: '#FFF',
                    fontWeight: '900',
                    fontSize: 16,
                    textAlign: 'center',
                    textTransform: 'capitalize',
                  }}
                >
                  {h}
                </Text>
              ))}
            </View>

            {/* Table Rows — filled */}
            {MOCK_DATA.map((row, i) => (
              <View
                key={i}
                style={{
                  flexDirection: 'row',
                  paddingVertical: 12,
                  borderBottomWidth: 1,
                  borderBottomColor: 'rgba(255,255,255,0.3)',
                }}
              >
                <Text style={{ flex: 1, color: '#FFF', textAlign: 'center', fontSize: 15 }}>
                  {row.name}
                </Text>
                <Text style={{ flex: 1, color: '#FFF', textAlign: 'center', fontSize: 15 }}>
                  {row.rank}
                </Text>
                <Text style={{ flex: 1, color: '#FFF', textAlign: 'center', fontSize: 15 }}>
                  {row.weight}
                </Text>
              </View>
            ))}

            {/* Empty rows */}
            {Array.from({ length: 6 }).map((_, i) => (
              <View
                key={`empty-${i}`}
                style={{
                  flexDirection: 'row',
                  paddingVertical: 16,
                  borderBottomWidth: 1,
                  borderBottomColor: 'rgba(255,255,255,0.2)',
                }}
              >
                <Text style={{ flex: 1 }} />
                <Text style={{ flex: 1 }} />
                <Text style={{ flex: 1 }} />
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
