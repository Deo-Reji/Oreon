import { useRef, useState } from 'react';
import { useCameraPermissions } from 'expo-camera';

export function useCamera() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [facing, setFacing] = useState('back');
  const [torch, setTorch] = useState(false);

  function flipCamera() {
    setFacing(prev => (prev === 'back' ? 'front' : 'back'));
  }

  function toggleTorch() {
    setTorch(prev => !prev);
  }

  async function startRecording() {
    if (!cameraRef.current || isRecording) return null;
    setIsRecording(true);
    try {
      const video = await cameraRef.current.recordAsync({ maxDuration: 60 });
      return video;
    } finally {
      setIsRecording(false);
    }
  }

  function stopRecording() {
    if (!cameraRef.current || !isRecording) return;
    cameraRef.current.stopRecording();
  }

  return {
    cameraRef,
    permission,
    requestPermission,
    isRecording,
    facing,
    flipCamera,
    torch,
    toggleTorch,
    startRecording,
    stopRecording,
  };
}
