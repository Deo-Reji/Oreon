import React from 'react';
import { View, Text, TextInput } from 'react-native';

const MAGENTA = '#CC00FF';

export const LabeledInput = ({ label, style = {}, inputStyle = {}, ...props }) => (
  <View style={style}>
    {label ? (
      <Text
        style={{
          color: '#000',
          fontWeight: '700',
          fontSize: 13,
          marginBottom: 6,
          textAlign: 'center',
        }}
      >
        {label}
      </Text>
    ) : null}
    <TextInput
      placeholderTextColor="#9900CC"
      style={[
        {
          backgroundColor: MAGENTA,
          borderRadius: 25,
          paddingVertical: 14,
          paddingHorizontal: 16,
          color: '#FFF',
          fontWeight: '700',
          fontSize: 14,
        },
        inputStyle,
      ]}
      {...props}
    />
  </View>
);
