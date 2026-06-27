import { apiRequest } from './apiClient';

export async function uploadVideo(videoUri, exercise) {
  const form = new FormData();
  form.append('video', {
    uri: videoUri,
    name: 'workout.mp4',
    type: 'video/mp4',
  });
  form.append('exercise', exercise);
  return apiRequest('/api/analyze', { method: 'POST', body: form, isForm: true });
}
