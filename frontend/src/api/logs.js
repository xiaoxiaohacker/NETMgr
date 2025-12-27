import axios from '@/utils/request'

export const getLogs = (params) => {
  return axios.get('/api/v1/logs/', { params })
}

export const exportLogs = (params) => {
  return axios.get('/api/v1/logs/export', { params, responseType: 'blob' })
}