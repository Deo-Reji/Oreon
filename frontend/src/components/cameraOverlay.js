import React from 'react';
import { View } from 'react-native';
import { useLevel } from '../hooks/useLevel';

const CYAN = '#00DFFF';

// Apple-style bubble level: two short fixed side marks, plus a center line
// that stays aligned to gravity (rotates opposite to device roll). When the
// camera is level the center line meets the side marks and glows cyan.
// Self-contained: subscribes to the accelerometer internally so the parent
// camera screen never re-renders on tilt changes.
export function LevelIndicator() {
  const { roll, isLevel } = useLevel(true);
  const color = isLevel ? CYAN : 'rgba(255,255,255,0.85)';
  const THICK = 2; // line thickness
  const SIDE = 24; // length of each fixed side mark
  const CENTER = 60; // length of the rotating center line

  return (
    <View
      pointerEvents="none"
      style={{ width: 220, height: 80, alignItems: 'center', justifyContent: 'center' }}
    >
      {/* Fixed side marks (locked to the device frame) */}
      <View style={{ position: 'absolute', left: 20, width: SIDE, height: THICK, borderRadius: 1, backgroundColor: color }} />
      <View style={{ position: 'absolute', right: 20, width: SIDE, height: THICK, borderRadius: 1, backgroundColor: color }} />

      {/* Center line — counter-rotates to stay level with the horizon */}
      <View
        style={{
          width: CENTER,
          height: THICK,
          borderRadius: 1,
          backgroundColor: color,
          transform: [{ rotate: `${-roll}deg` }],
          shadowColor: CYAN,
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: isLevel ? 1 : 0,
          shadowRadius: isLevel ? 8 : 0,
          elevation: isLevel ? 6 : 0,
        }}
      />
    </View>
  );
}

// Rounded framing guide marking where the user should stand in frame.
// Sized by the parent so it can be portrait-tall or landscape-wide.
export function FrameGuide({ width, height }) {
  return (
    <View
      pointerEvents="none"
      style={{
        width,
        height,
        borderWidth: 3,
        borderColor: CYAN,
        borderRadius: 44,
        shadowColor: CYAN,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 12,
        elevation: 6,
      }}
    />
  );
}
