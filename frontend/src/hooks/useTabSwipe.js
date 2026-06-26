import { useRef, useEffect } from 'react';
import { PanResponder } from 'react-native';

const TAB_ROUTES = ['MasteryScreen', 'HomeScreen', 'AccountSettings', 'SubscriptionsScreen'];

export const useTabSwipe = (activeIndex, navigation) => {
  const indexRef = useRef(activeIndex);
  const navRef = useRef(navigation);

  useEffect(() => { indexRef.current = activeIndex; }, [activeIndex]);
  useEffect(() => { navRef.current = navigation; }, [navigation]);

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, { dx, dy }) =>
        Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 20,
      onPanResponderRelease: (_, { dx }) => {
        const idx = indexRef.current;
        if (dx < -50 && idx < TAB_ROUTES.length - 1) {
          navRef.current.navigate(TAB_ROUTES[idx + 1]);
        } else if (dx > 50 && idx > 0) {
          navRef.current.navigate(TAB_ROUTES[idx - 1]);
        }
      },
    })
  ).current;

  return panResponder.panHandlers;
};
