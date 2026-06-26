import React from 'react';
import { TouchableOpacity, View, Text, Alert } from 'react-native';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

export const FeatureCard = ({ title, subtitle, color = CYAN, onPress, arrow = true }) => (
  <TouchableOpacity
    onPress={onPress || (() => Alert.alert('Feature', title))}
    activeOpacity={0.85}
    style={{
      backgroundColor: color,
      borderRadius: 14,
      padding: 22,
      marginBottom: 16,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}
  >
    <View style={{ flex: 1 }}>
      <Text
        style={{
          color: '#FFF',
          fontWeight: '900',
          fontSize: 22,
          textTransform: 'uppercase',
          letterSpacing: 1,
        }}
      >
        {title}
      </Text>
      {subtitle ? (
        <Text
          style={{
            color: '#FFF',
            fontWeight: '700',
            fontSize: 15,
            textTransform: 'uppercase',
            marginTop: 10,
            letterSpacing: 0.5,
          }}
        >
          {subtitle}
        </Text>
      ) : null}
    </View>
    {arrow && (
      <Text style={{ color: '#FFF', fontSize: 30, fontWeight: '700', marginLeft: 8 }}>›</Text>
    )}
  </TouchableOpacity>
);

export const ExerciseCard = ({ title, color = CYAN, onPress }) => (
  <TouchableOpacity
    onPress={onPress || (() => Alert.alert('Exercise', title))}
    activeOpacity={0.85}
    style={{
      backgroundColor: color,
      borderRadius: 30,
      paddingVertical: 16,
      paddingHorizontal: 24,
      marginBottom: 12,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}
  >
    <Text
      style={{
        color: '#FFF',
        fontWeight: '900',
        fontSize: 18,
        textTransform: 'uppercase',
        letterSpacing: 1,
      }}
    >
      {title}
    </Text>
    <Text style={{ color: '#FFF', fontSize: 22, fontWeight: '700' }}>›</Text>
  </TouchableOpacity>
);
