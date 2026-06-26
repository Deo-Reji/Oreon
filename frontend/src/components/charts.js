import React from 'react';
import { View, Text } from 'react-native';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

export const DonutChart = ({ percentage = 87, size = 140 }) => {
  const outer = size;
  const inner = size * 0.55;
  const cyanDeg = (percentage / 100) * 360;

  return (
    <View style={{ width: outer, height: outer, alignItems: 'center', justifyContent: 'center' }}>
      {/* Magenta base ring */}
      <View
        style={{
          position: 'absolute',
          width: outer,
          height: outer,
          borderRadius: outer / 2,
          backgroundColor: MAGENTA,
        }}
      />
      {/* Cyan progress arc overlay */}
      <View
        style={{
          position: 'absolute',
          width: outer,
          height: outer,
          borderRadius: outer / 2,
          overflow: 'hidden',
        }}
      >
        <View
          style={{
            width: outer / 2,
            height: outer,
            backgroundColor: percentage > 50 ? CYAN : 'transparent',
            position: 'absolute',
            right: 0,
          }}
        />
        {percentage <= 50 && (
          <View
            style={{
              width: outer / 2,
              height: outer,
              backgroundColor: CYAN,
              position: 'absolute',
              right: 0,
              transform: [{ rotate: `${cyanDeg - 180}deg` }],
              transformOrigin: 'left center',
            }}
          />
        )}
      </View>
      {/* Black inner circle */}
      <View
        style={{
          width: inner,
          height: inner,
          borderRadius: inner / 2,
          backgroundColor: '#000',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1,
        }}
      >
        <Text style={{ color: '#FFF', fontWeight: '900', fontSize: 22 }}>{percentage}%</Text>
      </View>
    </View>
  );
};

export const SimpleBarChart = ({
  data = [
    { s1: 3, s2: 5 },
    { s1: 10, s2: 14 },
    { s1: 15, s2: 18 },
  ],
  height = 100,
}) => {
  const maxVal = Math.max(...data.flatMap(d => [d.s1, d.s2]));
  return (
    <View>
      <View style={{ flexDirection: 'row', alignItems: 'flex-end', height, gap: 8 }}>
        {data.map((item, i) => (
          <View key={i} style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 3 }}>
            <View
              style={{
                width: 14,
                height: (item.s1 / maxVal) * (height - 10),
                backgroundColor: CYAN,
                borderRadius: 2,
              }}
            />
            <View
              style={{
                width: 14,
                height: (item.s2 / maxVal) * (height - 10),
                backgroundColor: MAGENTA,
                borderRadius: 2,
              }}
            />
          </View>
        ))}
      </View>
      {/* Legend */}
      <View style={{ flexDirection: 'row', gap: 16, marginTop: 8 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
          <View style={{ width: 10, height: 10, backgroundColor: CYAN, borderRadius: 2 }} />
          <Text style={{ color: '#FFF', fontSize: 10 }}>Series 1</Text>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
          <View style={{ width: 10, height: 10, backgroundColor: MAGENTA, borderRadius: 2 }} />
          <Text style={{ color: '#FFF', fontSize: 10 }}>Series 2</Text>
        </View>
      </View>
    </View>
  );
};
