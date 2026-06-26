import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  StatusBar,
} from 'react-native';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

export default function WorkoutSession({ navigation, route }) {
  const { exerciseName = 'Squat' } = route?.params ?? {};
  const [reps, setReps] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const totalTime = 60;

  useEffect(() => {
    if (!isRecording) return;
    const interval = setInterval(() => {
      setElapsed(prev => {
        if (prev >= totalTime) {
          clearInterval(interval);
          setIsRecording(false);
          navigation.navigate('FormResults');
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isRecording]);

  const formatTime = secs => {
    const m = String(Math.floor(secs / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFF' }}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFF" />

      {/* Top toolbar */}
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingHorizontal: 20,
          paddingTop: 12,
          paddingBottom: 8,
          backgroundColor: '#FFF',
        }}
      >
        {/* Back */}
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ color: '#000', fontSize: 32, fontWeight: '700', lineHeight: 36 }}>‹</Text>
        </TouchableOpacity>

        {/* Tools */}
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16 }}>
          <TouchableOpacity onPress={() => Alert.alert('Flashlight', 'Toggle flashlight')}>
            <Text style={{ fontSize: 28 }}>🔦</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => Alert.alert('Level', 'Toggle level tool')}>
            <Text style={{ fontSize: 24 }}>📏</Text>
          </TouchableOpacity>
        </View>

        {/* Stopwatch */}
        <TouchableOpacity onPress={() => Alert.alert('Stopwatch', 'Open stopwatch')}>
          <Text style={{ fontSize: 30 }}>⏱</Text>
        </TouchableOpacity>
      </View>

      {/* Camera Viewfinder */}
      <View style={{ flex: 1, paddingHorizontal: 20, paddingVertical: 12 }}>
        <View
          style={{
            flex: 1,
            borderWidth: 3,
            borderColor: CYAN,
            borderRadius: 16,
            overflow: 'hidden',
            backgroundColor: '#EEF6FF',
            alignItems: 'center',
            justifyContent: 'center',
            shadowColor: CYAN,
            shadowOffset: { width: 0, height: 0 },
            shadowOpacity: 0.7,
            shadowRadius: 12,
            elevation: 8,
          }}
        >
          {/* Corner decorations */}
          {[
            { top: 8, left: 8 },
            { top: 8, right: 8 },
            { bottom: 8, left: 8 },
            { bottom: 8, right: 8 },
          ].map((pos, i) => (
            <View
              key={i}
              style={{
                position: 'absolute',
                ...pos,
                width: 20,
                height: 20,
                borderColor: CYAN,
                borderTopWidth: pos.top !== undefined ? 3 : 0,
                borderBottomWidth: pos.bottom !== undefined ? 3 : 0,
                borderLeftWidth: pos.left !== undefined ? 3 : 0,
                borderRightWidth: pos.right !== undefined ? 3 : 0,
              }}
            />
          ))}
          {/*
            Replace with camera view:
            <Camera style={{ flex: 1, width: '100%' }} type={Camera.Constants.Type.front} />
          */}
          <Text style={{ fontSize: 100 }}>🏋️</Text>
        </View>
      </View>

      {/* Bottom controls */}
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-around',
          paddingHorizontal: 32,
          paddingVertical: 20,
          backgroundColor: '#FFF',
        }}
      >
        {/* Rep counter */}
        <TouchableOpacity onPress={() => setReps(prev => prev + 1)}>
          <View style={{ alignItems: 'center' }}>
            <Text style={{ fontSize: 64, fontWeight: '900', color: '#000', lineHeight: 70 }}>
              {reps}
            </Text>
            <Text style={{ fontSize: 18, fontWeight: '700', color: '#000' }}>Reps</Text>
          </View>
        </TouchableOpacity>

        {/* Record button + timer */}
        <TouchableOpacity
          onPress={() => {
            if (!isRecording) {
              setIsRecording(true);
            } else {
              setIsRecording(false);
              Alert.alert('Stopped', 'Recording paused');
            }
          }}
        >
          <View style={{ alignItems: 'center' }}>
            <Text style={{ fontSize: 44 }}>
              {isRecording ? '🔴' : '📹'}
            </Text>
            <Text style={{ fontSize: 16, fontWeight: '900', color: '#000', marginTop: 2 }}>
              REC
            </Text>
            <Text style={{ fontSize: 14, fontWeight: '700', color: '#000' }}>
              {formatTime(elapsed)}/{formatTime(totalTime)}
            </Text>
          </View>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
