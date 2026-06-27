import { useState } from 'react';
import { uploadVideo } from '../services/analysisService';

export function useAnalysis() {
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  async function analyze(videoUri, exercise) {
    setAnalyzing(true);
    setError(null);
    try {
      const data = await uploadVideo(videoUri, exercise);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setAnalyzing(false);
    }
  }

  return { analyzing, error, analyze };
}
