import React from 'react';
import { TouchableOpacity, Text } from 'react-native';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';
const YELLOW = '#FFD700';
const BLUE = '#0A84FF';

const labelStyle = {
  fontWeight: '900',
  textTransform: 'uppercase',
  letterSpacing: 1,
  textAlign: 'center',
  fontSize: 18,
};

export const CyanButton = ({ title, onPress, style = {} }) => (
  <TouchableOpacity
    onPress={onPress}
    activeOpacity={0.8}
    style={[
      {
        backgroundColor: CYAN,
        borderRadius: 30,
        paddingVertical: 16,
        paddingHorizontal: 20,
        alignItems: 'center',
        shadowColor: CYAN,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 12,
        elevation: 8,
      },
      style,
    ]}
  >
    <Text style={{ ...labelStyle, color: '#FFF' }}>{title}</Text>
  </TouchableOpacity>
);

export const MagentaButton = ({ title, onPress, style = {} }) => (
  <TouchableOpacity
    onPress={onPress}
    activeOpacity={0.8}
    style={[
      {
        backgroundColor: MAGENTA,
        borderRadius: 30,
        paddingVertical: 16,
        paddingHorizontal: 20,
        alignItems: 'center',
        shadowColor: MAGENTA,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 12,
        elevation: 8,
      },
      style,
    ]}
  >
    <Text style={{ ...labelStyle, color: '#FFF' }}>{title}</Text>
  </TouchableOpacity>
);

export const BlueButton = ({ title, onPress, style = {} }) => (
  <TouchableOpacity
    onPress={onPress}
    activeOpacity={0.8}
    style={[
      {
        backgroundColor: BLUE,
        borderRadius: 30,
        paddingVertical: 16,
        paddingHorizontal: 20,
        alignItems: 'center',
        shadowColor: BLUE,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 12,
        elevation: 8,
      },
      style,
    ]}
  >
    <Text style={{ ...labelStyle, color: '#FFF' }}>{title}</Text>
  </TouchableOpacity>
);

export const YellowButton = ({ title, onPress, style = {} }) => (
  <TouchableOpacity
    onPress={onPress}
    activeOpacity={0.8}
    style={[
      {
        backgroundColor: YELLOW,
        borderRadius: 20,
        paddingVertical: 14,
        paddingHorizontal: 28,
        alignItems: 'center',
        shadowColor: YELLOW,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.6,
        shadowRadius: 8,
        elevation: 6,
      },
      style,
    ]}
  >
    <Text style={{ ...labelStyle, color: '#000', fontSize: 16 }}>{title}</Text>
  </TouchableOpacity>
);
