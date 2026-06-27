import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Alert,
  StatusBar,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import { CameraView } from 'expo-camera';
import { useVideoPlayer, VideoView } from 'expo-video';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import * as ScreenOrientation from 'expo-screen-orientation';
import { useCamera } from '../../hooks/useCamera';
import { useAnalysis } from '../../hooks/useAnalysis';
import { LevelIndicator, FrameGuide } from '../../components/cameraOverlay';
import { CyanButton, MagentaButton } from '../../components/buttons';

const CYAN = '#00DFFF';
const TOTAL_TIME = 60;

// Round toolbar button. Defined at module scope so it isn't remounted on
// every parent re-render (which would swallow the first tap).
function IconButton({ name, onPress, active, disabled }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
      style={{
        width: 48,
        height: 48,
        borderRadius: 24,
        opacity: disabled ? 0.4 : 1,
        backgroundColor: active ? CYAN : 'rgba(0,0,0,0.45)',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: active ? CYAN : 'rgba(0,223,255,0.5)',
      }}
    >
      <Ionicons name={name} size={24} color={active ? '#000' : '#FFF'} />
    </TouchableOpacity>
  );
}

// Blue circle record button (becomes a stop square while recording).
function RecordButton({ isRecording, analyzing, onPress }) {
  return (
    <TouchableOpacity onPress={onPress} disabled={analyzing} activeOpacity={0.8} hitSlop={12}>
      <View
        style={{
          width: 76,
          height: 76,
          borderRadius: 38,
          borderWidth: 4,
          borderColor: CYAN,
          alignItems: 'center',
          justifyContent: 'center',
          shadowColor: CYAN,
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 0.8,
          shadowRadius: 10,
          elevation: 8,
        }}
      >
        <View
          style={{
            width: isRecording ? 28 : 58,
            height: isRecording ? 28 : 58,
            borderRadius: isRecording ? 6 : 29,
            backgroundColor: CYAN,
          }}
        />
      </View>
    </TouchableOpacity>
  );
}

// Looping playback of the just-recorded clip for the review step. Mounted only
// while a preview exists, so the player is created fresh for each take.
function VideoPreview({ uri }) {
  const player = useVideoPlayer(uri, p => {
    p.loop = true;
    p.play();
  });
  return (
    <VideoView
      player={player}
      style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      contentFit="contain"
      nativeControls={false}
    />
  );
}

export default function WorkoutSession({ navigation, route }) {
  const { exerciseName = 'squat' } = route?.params ?? {};
  const [elapsed, setElapsed] = useState(0);
  const [previewUri, setPreviewUri] = useState(null);
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;
  // Portrait: keep side margins, stretch top/bottom. Landscape: the inverse.
  const boxW = isLandscape ? width * 0.78 : width * 0.84;
  const boxH = isLandscape ? height * 0.84 : height * 0.72;

  const {
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
  } = useCamera();
  const { analyzing, analyze } = useAnalysis();

  // Let this screen rotate freely while focused, then restore the app-wide
  // portrait lock on blur (native-stack keeps the screen mounted, so this
  // must hang off focus rather than mount/unmount).
  useFocusEffect(
    useCallback(() => {
      setPreviewUri(null);
      setElapsed(0);
      ScreenOrientation.unlockAsync();
      return () => {
        ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP);
      };
    }, [])
  );

  useEffect(() => {
    if (!isRecording) return;
    const interval = setInterval(() => {
      setElapsed(prev => {
        if (prev >= TOTAL_TIME) {
          clearInterval(interval);
          stopRecording();
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

  async function handleToggleRecord() {
    if (analyzing) return;

    if (isRecording) {
      stopRecording();
      return;
    }

    setElapsed(0);
    // Pin the orientation for the whole record+review pass so the clip can't
    // switch aspect ratio mid-set (analysis needs one consistent format).
    await ScreenOrientation.lockAsync(
      isLandscape ? ScreenOrientation.OrientationLock.LANDSCAPE : ScreenOrientation.OrientationLock.PORTRAIT_UP
    );
    try {
      const video = await startRecording();
      if (!video?.uri) {
        await ScreenOrientation.unlockAsync();
        return;
      }
      // Show the review step instead of analyzing immediately.
      setPreviewUri(video.uri);
    } catch (err) {
      await ScreenOrientation.unlockAsync();
      Alert.alert('Recording failed', err.message ?? 'Something went wrong. Try again.');
    }
  }

  // Discard the clip and return to the live camera (orientation freed so the
  // next take can use a different format).
  async function handleRetake() {
    setPreviewUri(null);
    setElapsed(0);
    await ScreenOrientation.unlockAsync();
  }

  // Submit the reviewed clip for analysis, then show results.
  async function handleSubmit() {
    if (analyzing) return;
    try {
      const data = await analyze(previewUri, exerciseName.toLowerCase());
      navigation.navigate('FormResults', {
        score: data.form_score,
        reps: data.reps,
        exercise: exerciseName,
      });
    } catch (err) {
      Alert.alert('Analysis failed', err.message ?? 'Something went wrong. Try again.');
    }
  }

  if (!permission) {
    return <View style={{ flex: 1, backgroundColor: '#000' }} />;
  }

  if (!permission.granted) {
    return (
      <View style={{ flex: 1, backgroundColor: '#000', alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: '#FFF', fontSize: 18, marginBottom: 24, textAlign: 'center', paddingHorizontal: 32 }}>
          Camera access is needed to record your workout.
        </Text>
        <TouchableOpacity
          onPress={requestPermission}
          style={{ backgroundColor: CYAN, paddingHorizontal: 32, paddingVertical: 12, borderRadius: 12 }}
        >
          <Text style={{ color: '#000', fontWeight: '900', fontSize: 16 }}>Allow Camera</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <StatusBar hidden />

      {/* Fullscreen camera */}
      <CameraView
        ref={cameraRef}
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        facing={facing}
        mode="video"
        enableTorch={torch}
        mute
      />

      {/* Center framing guide + bubble level */}
      <View
        pointerEvents="none"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <FrameGuide width={boxW} height={boxH} />
        <View style={{ position: 'absolute' }}>
          <LevelIndicator />
        </View>
      </View>

      {/* Top bar: back arrow + exercise name. In landscape they're placed
          independently (back lower-left, name higher) to clear the box. */}
      {isLandscape ? (
        <>
          <View style={{ position: 'absolute', top: insets.top + 35, left: 20 }}>
            <IconButton name="chevron-back" onPress={() => !isRecording && !analyzing && navigation.goBack()} />
          </View>
          <Text
            style={{
              position: 'absolute',
              top: insets.top + 6,
              left: 0,
              right: 0,
              textAlign: 'center',
              color: '#FFF',
              fontWeight: '900',
              fontSize: 16,
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            {exerciseName}
          </Text>
        </>
      ) : (
        <View
          style={{
            position: 'absolute',
            top: insets.top + 6,
            left: insets.left + 16,
            right: insets.right + 16,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <IconButton name="chevron-back" onPress={() => !isRecording && !analyzing && navigation.goBack()} />
          <Text
            style={{
              flex: 1,
              textAlign: 'center',
              color: '#FFF',
              fontWeight: '900',
              fontSize: 16,
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            {exerciseName}
          </Text>
          {/* Spacer to balance the back button so the name stays centered */}
          <View style={{ width: 48 }} />
        </View>
      )}

      {/* Controls: bottom row in portrait, right-side column in landscape.
          Camera flip is locked while recording so the format can't change. */}
      <View
        style={
          isLandscape
            ? { position: 'absolute', right: 8, top: 0, bottom: 0, justifyContent: 'center', alignItems: 'center' }
            : { position: 'absolute', bottom: insets.bottom + 0, left: 0, right: 0, alignItems: 'center' }
        }
      >
        {/* Portrait: timer pill above the row. */}
        {!isLandscape && isRecording && (
          <View
            style={{
              backgroundColor: 'rgba(0,0,0,0.5)',
              paddingHorizontal: 14,
              paddingVertical: 5,
              borderRadius: 14,
              flexDirection: 'row',
              alignItems: 'center',
              gap: 6,
              marginBottom: 20,
            }}
          >
            <View style={{ width: 9, height: 9, borderRadius: 5, backgroundColor: '#FF3B30' }} />
            <Text style={{ color: '#FFF', fontWeight: '800', fontSize: 14 }}>
              {formatTime(elapsed)} / {formatTime(TOTAL_TIME)}
            </Text>
          </View>
        )}

        <View
          style={{
            flexDirection: isLandscape ? 'column' : 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: isLandscape ? 24 : 32,
          }}
        >
          <IconButton name={torch ? 'flashlight' : 'flashlight-outline'} onPress={toggleTorch} active={torch} />
          <View style={{ alignItems: 'center', justifyContent: 'center' }}>
            {/* Landscape: vertical recording line beside the record button that
                fills as the clip progresses (absolute, so icons don't shift). */}
            {isLandscape && isRecording && (
              <View
                style={{
                  position: 'absolute',
                  right: 100,
                  width: 10,
                  height: 76,
                  borderRadius: 3,
                  backgroundColor: 'rgba(255,255,255,0.25)',
                  overflow: 'hidden',
                  justifyContent: 'flex-end',
                }}
              >
                <View
                  style={{
                    width: '100%',
                    height: `${(elapsed / TOTAL_TIME) * 100}%`,
                    backgroundColor: '#FF3B30',
                    borderRadius: 3,
                  }}
                />
              </View>
            )}
            <RecordButton isRecording={isRecording} analyzing={analyzing} onPress={handleToggleRecord} />
          </View>
          <IconButton name="camera-reverse-outline" onPress={flipCamera} disabled={isRecording} />
        </View>
      </View>

      {/* Review step: rewatch the clip, then retake or submit for analysis */}
      {previewUri && (
        <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: '#000' }}>
          <VideoPreview uri={previewUri} />
          <View
            style={
              isLandscape
                ? { position: 'absolute', right: 24, top: 0, bottom: 0, alignItems: 'center', justifyContent: 'center', gap: 20 }
                : { position: 'absolute', bottom: insets.bottom + -20, left: 24, right: 24, flexDirection: 'row', justifyContent: 'center', gap: 16 }
            }
          >
            <MagentaButton
              title={isLandscape ? 'Retake'.split('').join('\n') : 'Retake'}
              onPress={handleRetake}
              style={isLandscape ? { width: 40, paddingVertical: 10, paddingHorizontal: 6 } : { flex: 1 }}
              textStyle={isLandscape ? { fontSize: 12, lineHeight: 14, letterSpacing: 0 } : {}}
            />
            <CyanButton
              title={isLandscape ? 'Analyze'.split('').join('\n') : 'Analyze'}
              onPress={handleSubmit}
              disabled={analyzing}
              style={isLandscape ? { width: 40, paddingVertical: 10, paddingHorizontal: 6 } : { flex: 1 }}
              textStyle={isLandscape ? { fontSize: 12, lineHeight: 14, letterSpacing: 0 } : {}}
            />
          </View>
        </View>
      )}

      {/* Analyzing overlay */}
      {analyzing && (
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.65)',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ActivityIndicator size="large" color={CYAN} />
          <Text style={{ color: '#FFF', marginTop: 12, fontWeight: '700', fontSize: 16 }}>Analyzing...</Text>
        </View>
      )}
    </View>
  );
}
