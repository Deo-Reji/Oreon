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
import { ExerciseCard } from '../../components/cards';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const GYM_DATA = [
  {
    id: 'chest',
    label: 'Chest',
    exercises: [
      { name: 'Bench Press', color: CYAN },
      { name: 'Chest Fly', color: MAGENTA },
    ],
  },
  {
    id: 'biceps',
    label: 'Biceps',
    exercises: [
      { name: 'Hammer Curl', color: CYAN },
      { name: 'Preacher Curl', color: MAGENTA },
    ],
  },
  {
    id: 'legs',
    label: 'Legs',
    exercises: [
      { name: 'Leg Press', color: CYAN },
      { name: 'Squat', color: MAGENTA },
    ],
  },
];

export default function ExerciseList({ navigation }) {
  const [expanded, setExpanded] = useState({ chest: true, biceps: true, legs: true });

  const toggle = id => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }}>

        {/* Header Row */}
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
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
                fontSize: 38,
                textTransform: 'uppercase',
                letterSpacing: 3,
              },
            ]}
          >
            Gym
          </Text>
        </View>

        <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 20 }}>
          {GYM_DATA.map(group => (
            <View key={group.id} style={{ marginBottom: 16 }}>
              {/* Category Header */}
              <TouchableOpacity
                onPress={() => toggle(group.id)}
                style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}
              >
                <Text
                  style={{
                    color: '#FFF',
                    fontWeight: '900',
                    fontSize: 26,
                    textTransform: 'uppercase',
                    letterSpacing: 2,
                    marginRight: 10,
                  }}
                >
                  {group.label}
                </Text>
                <Text style={{ color: '#FFF', fontSize: 26, fontWeight: '900', letterSpacing: 2 }}>
                  {expanded[group.id] ? '▼' : '›'}
                </Text>
              </TouchableOpacity>

              {/* Exercise cards */}
              {expanded[group.id] &&
                group.exercises.map(ex => (
                  <ExerciseCard
                    key={ex.name}
                    title={ex.name}
                    color={ex.color}
                    onPress={() =>
                      navigation.navigate('ExerciseDetail', { exerciseName: ex.name })
                    }
                  />
                ))}
            </View>
          ))}
        </ScrollView>

        <BottomNav activeIndex={1} />
      </View>
    </SafeAreaView>
  );
}
