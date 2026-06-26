import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  SafeAreaView,
  ScrollView,
  TextInput,
  StatusBar,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { MagentaButton } from '../../components/buttons';

const CYAN = '#00DFFF';
const MAGENTA = '#CC00FF';

const glowText = {
  textShadowColor: '#FFFFFF',
  textShadowOffset: { width: 0, height: 0 },
  textShadowRadius: 18,
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);
const YEARS = Array.from({ length: 2012 - 1920 + 1 }, (_, i) => 1920 + i);
const FEET = [3, 4, 5, 6, 7, 8];
const INCHES = Array.from({ length: 12 }, (_, i) => i);

const fieldStyle = {
  backgroundColor: MAGENTA,
  borderRadius: 25,
  paddingVertical: 14,
  paddingHorizontal: 16,
  color: '#FFF',
  fontWeight: '700',
  fontSize: 14,
  marginBottom: 4,
};

const labelStyle = {
  color: '#FFF',
  fontWeight: '900',
  fontSize: 13,
  textAlign: 'center',
  marginBottom: 6,
  marginTop: 12,
  textTransform: 'uppercase',
  letterSpacing: 1,
};

const PickerWheel = ({ selectedValue, onValueChange, items, labelKey = 'label', valueKey = 'value' }) => (
  <Picker
    selectedValue={selectedValue}
    onValueChange={onValueChange}
    style={{ flex: 1, color: '#FFF' }}
    itemStyle={{ color: '#FFF', fontSize: 16, fontWeight: '700' }}
    dropdownIconColor="#FFF"
  >
    {items.map((item, i) => {
      const label = typeof item === 'object' ? item[labelKey] : String(item);
      const value = typeof item === 'object' ? item[valueKey] : item;
      return <Picker.Item key={i} label={label} value={value} color="#FFF" />;
    })}
  </Picker>
);

export default function GettingStarted({ navigation }) {
  const [month, setMonth] = useState(1);
  const [day, setDay] = useState(1);
  const [year, setYear] = useState(1990);
  const [heightFt, setHeightFt] = useState(5);
  const [heightIn, setHeightIn] = useState(8);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} keyboardShouldPersistTaps="handled">
        <View style={{ paddingHorizontal: 20, paddingTop: 24, paddingBottom: 40 }}>

          <Image
            source={require('../../../assets/logo.png')}
            style={{ width: 56, height: 56, marginBottom: 20 }}
            resizeMode="contain"
          />

          <Text
            style={[
              glowText,
              {
                color: '#FFF',
                fontWeight: '900',
                fontSize: 38,
                textTransform: 'uppercase',
                letterSpacing: 2,
                textAlign: 'center',
                marginBottom: 20,
              },
            ]}
          >
            Getting Started
          </Text>

          {/* Form card */}
          <View style={{ backgroundColor: CYAN, borderRadius: 20, padding: 20 }}>

            {/* First Name */}
            <Text style={labelStyle}>First Name</Text>
            <TextInput
              placeholder="First Name"
              placeholderTextColor="#440066"
              style={fieldStyle}
            />

            {/* Middle Name */}
            <Text style={labelStyle}>Middle Name</Text>
            <TextInput
              placeholder="Middle Name"
              placeholderTextColor="#440066"
              style={fieldStyle}
            />

            {/* Last Name */}
            <Text style={labelStyle}>Last Name</Text>
            <TextInput
              placeholder="Last Name"
              placeholderTextColor="#440066"
              style={[fieldStyle, { marginBottom: 0 }]}
            />

            {/* Birthday */}
            <Text style={labelStyle}>Birthday</Text>
            <View
              style={{
                flexDirection: 'row',
                backgroundColor: MAGENTA,
                borderRadius: 16,
                overflow: 'hidden',
                height: 150,
              }}
            >
              <PickerWheel selectedValue={month} onValueChange={setMonth} items={MONTHS.map((m, i) => ({ label: m, value: i + 1 }))} />
              <View style={{ width: 1, backgroundColor: 'rgba(255,255,255,0.2)' }} />
              <PickerWheel selectedValue={day} onValueChange={setDay} items={DAYS} />
              <View style={{ width: 1, backgroundColor: 'rgba(255,255,255,0.2)' }} />
              <PickerWheel selectedValue={year} onValueChange={setYear} items={YEARS} />
            </View>

            {/* Email (verification added later) */}
            <Text style={labelStyle}>Email</Text>
            <TextInput
              placeholder="Email"
              placeholderTextColor="#440066"
              keyboardType="email-address"
              autoCapitalize="none"
              style={[fieldStyle, { marginBottom: 0 }]}
            />

            {/* Height */}
            <Text style={labelStyle}>Height</Text>
            <View
              style={{
                flexDirection: 'row',
                backgroundColor: MAGENTA,
                borderRadius: 16,
                overflow: 'hidden',
                height: 150,
              }}
            >
              <PickerWheel
                selectedValue={heightFt}
                onValueChange={setHeightFt}
                items={FEET.map(f => ({ label: `${f} ft`, value: f }))}
              />
              <View style={{ width: 1, backgroundColor: 'rgba(255,255,255,0.2)' }} />
              <PickerWheel
                selectedValue={heightIn}
                onValueChange={setHeightIn}
                items={INCHES.map(i => ({ label: `${i} in`, value: i }))}
              />
            </View>

            {/* Weight */}
            <Text style={labelStyle}>Weight (lbs)</Text>
            <TextInput
              placeholder="e.g. 165"
              placeholderTextColor="#440066"
              keyboardType="numeric"
              style={[fieldStyle, { marginBottom: 0 }]}
            />

          </View>

          <View style={{ marginTop: 24 }}>
            <MagentaButton
              title="Continue"
              onPress={() => navigation.navigate('HomeScreen')}
            />
          </View>

        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
