import request from './auth'  // 复用已有的 axios 实例（自动携带 JWT）

export const importEEGData = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/brain/api/import-eeg-data/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const analyzeExistingData = (recordingId: string, apiKey: string) => {
  return request.post('/brain/api/analyze-existing-data/', { recording_id: recordingId, api_key: apiKey })
}

export const testApiKey = (apiKey: string) => {
  return request.post('/brain/api/test-api-key/', { api_key: apiKey })
}

export const getLatestRecord = () => {
  return request.get('/brain/api/latest-eeg-record/')
}

export const getAllRecords = () => {
  return request.get('/brain/api/all-eeg-records/')
}