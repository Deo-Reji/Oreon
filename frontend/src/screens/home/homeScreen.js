import React from 'react';
import { View, Text, Image, SafeAreaView, ScrollView, Alert, StatusBar } from 'react-native';
import { BottomNav } from '../../components/navigation';
import { FeatureCard } from '../../components/cards';
import { useTabSwipe } from '../../hooks/useTabSwipe';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

export default function HomeScreen({ navigation }) {
  const panHandlers = useTabSwipe(1, navigation);
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <View style={{ flex: 1 }} {...panHandlers}>

        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
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
                fontSize: 44,
                textTransform: 'uppercase',
                letterSpacing: 3,
                textAlign: 'center',
                marginVertical: 20,
              },
            ]}
          >
            Featured
          </Text>

          <FeatureCard
            title="Gym:"
            subtitle="Perfect Various Exercises"
            color={CYAN}
            onPress={() => navigation.navigate('ExerciseList')}
          />

          <FeatureCard
            title="Basketball:"
            subtitle="Perfect Your Shooting Form"
            color={MAGENTA}
            onPress={() => Alert.alert('Basketball', 'Coming soon!')}
          />

          <FeatureCard
            title="More Coming Soon"
            color={CYAN}
            onPress={() => Alert.alert('Coming Soon', 'More sports coming soon!')}
            arrow={false}
          />
        </ScrollView>

        <BottomNav activeIndex={1} />
      </View>
    </SafeAreaView>
  );
}
