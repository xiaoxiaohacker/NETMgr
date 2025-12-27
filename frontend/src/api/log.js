import request from '@/utils/request'

/**
 * 获取系统日志列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getSystemLogs(params) {
  return request({
    url: '/api/v1/logs/',
    method: 'get',
    params
  })
}

/**
 * 导出系统日志
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function exportSystemLogs(params) {
  return request({
    url: '/api/v1/logs/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

/**
 * 获取所有日志级别
 * @returns {Promise}
 */
export function getLogLevels() {
  return request({
    url: '/api/v1/logs/levels',
    method: 'get'
  })
}

/**
 * 获取所有日志模块
 * @returns {Promise}
 */
export function getLogModules() {
  return request({
    url: '/api/v1/logs/modules',
    method: 'get'
  })
}