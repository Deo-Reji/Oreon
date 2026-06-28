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
import { MagentaButton, CyanButton } from '../../components/buttons';
import { DonutChart, SimpleBarChart } from '../../components/charts';

const MAGENTA = '#CC00FF';
const CYAN = '#00DFFF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

export default function FormResults({ navigation, route }) {
  const {
    score: rawScore = 0,
    reps = 0,
    exercise = '',
    grade = '',
    improvements = [],
  } = route?.params ?? {};
  const score = Math.min(Math.round(rawScore), 100);
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }}>

        {/* Logo */}
        <View style={{ paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
          <Image source={require('../../../assets/logo.png')} style={{ width: 50, height: 50 }} resizeMode="contain" />
        </View>

        <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 20 }}>
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
                textAlign: 'center',
                lineHeight: 46,
                marginBottom: 8,
              },
            ]}
          >
            Your Form{'\n'}Results
          </Text>
          {exercise ? (
            <Text style={{ color: '#AAA', fontSize: 14, textAlign: 'center', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              {exercise}
            </Text>
          ) : null}
          <Text style={[glowText, { color: '#FFF', fontSize: 20, fontWeight: '900', textAlign: 'center', marginBottom: grade ? 6 : 20 }]}>
            {reps} {reps === 1 ? 'Rep' : 'Reps'}
          </Text>
          {grade ? (
            <Text style={[glowText, { color: CYAN, fontSize: 26, fontWeight: '900', textAlign: 'center', marginBottom: 20, letterSpacing: 1 }]}>
              Grade: {grade}
            </Text>
          ) : null}

          {/* Charts row */}
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 32,
            }}
          >
            <DonutChart percentage={score} size={140} />
            <SimpleBarChart
              data={[
                { s1: 3, s2: 5 },
                { s1: 10, s2: 14 },
                { s1: 15, s2: 18 },
              ]}
              height={110}
            />
          </View>

          {/* Things to Improve */}
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
            Things to Improve:
          </Text>
          {improvements.length === 0 ? (
            <Text
              style={[
                glowText,
                { color: '#FFF', fontWeight: '800', fontSize: 18, letterSpacing: 1 },
              ]}
            >
              Clean reps — no major faults detected.
            </Text>
          ) : (
            improvements.map(item => (
              <View key={item} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
                <Text style={[glowText, { color: '#FFF', fontSize: 18, fontWeight: '900', marginRight: 10 }]}>
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
                  {item}
                </Text>
              </View>
            ))
          )}

          {/* Action Buttons */}
          <View style={{ marginTop: 32, gap: 16 }}>
            <MagentaButton
              title="Review Video Footage"
              onPress={() => Alert.alert('Review', 'Open video playback')}
            />
            <CyanButton
              title="Try Again"
              onPress={() => navigation.goBack()}
            />
          </View>
        </ScrollView>

        <BottomNav activeIndex={1} />
      </View>
    </SafeAreaView>
  );
}
