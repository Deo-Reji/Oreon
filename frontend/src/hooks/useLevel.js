import { useEffect, useState } from 'react';
import { Accelerometer } from 'expo-sensors';

// Returns the device's deviation from level in degrees, plus an `isLevel`
// flag. We measure the raw roll about the camera's viewing axis, then subtract
// the nearest cardinal angle (0/±90/180). That makes "level" work in portrait
// AND both landscape directions without depending on the orientation enum.
export function useLevel(active = true) {
  const [state, setState] = useState({ roll: 0, isLevel: false });

  useEffect(() => {
    if (!active) return;
    Accelerometer.setUpdateInterval(80);
    const sub = Accelerometer.addListener(({ x, y }) => {
      const phi = (Math.atan2(x, -y) * 180) / Math.PI; // raw roll, -180..180
      const baseline = Math.round(phi / 90) * 90;        // nearest cardinal
      const roll = phi - baseline;                       // deviation, ~-45..45
      const isLevel = Math.abs(roll) < 1.5;
      setState({ roll, isLevel });
    });
    return () => sub.remove();
  }, [active]);

  return state;
}
