import React from 'react';
import { View, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';

const MAGENTA_ACTIVE = '#CC00FF';
const MAGENTA_INACTIVE = '#4A0072';

const TAB_ROUTES = ['MasteryScreen', 'HomeScreen', 'AccountSettings', 'SubscriptionsScreen'];

export const BottomNav = ({ activeIndex = 1 }) => {
  const navigation = useNavigation();
  const tabs = ['Mastery', 'Home', 'Account', 'Subscriptions'];

  return (
    <View
      style={{
        flexDirection: 'row',
        justifyContent: 'space-around',
        alignItems: 'center',
        paddingTop: 12,
        paddingBottom: 32,
        borderTopWidth: 1,
        borderTopColor: '#222',
        backgroundColor: '#000',
      }}
    >
      {tabs.map((tab, i) => (
        <TouchableOpacity
          key={i}
          onPress={() => navigation.navigate(TAB_ROUTES[i])}
          activeOpacity={0.7}
        >
          <View
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              backgroundColor: i === activeIndex ? MAGENTA_ACTIVE : MAGENTA_INACTIVE,
            }}
          />
        </TouchableOpacity>
      ))}
    </View>
  );
};
