import request from '@/utils/request'

/**
 * 获取告警统计信息
 * @returns {Promise}
 */
export function getAlertStatistics() {
  return request({
    url: '/api/v1/alerts/statistics',
    method: 'get'
  })
}

/**
 * 获取告警列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getAlerts(params) {
  return request({
    url: '/api/v1/alerts/',
    method: 'get',
    params
  })
}

/**
 * 标记告警为已解决
 * @param {number} id 告警ID
 * @returns {Promise}
 */
export function resolveAlert(id) {
  return request({
    url: `/api/v1/alerts/${id}/resolve`,
    method: 'put'
  })
}

/**
 * 删除告警
 * @param {number} id 告警ID
 * @returns {Promise}
 */
export function deleteAlert(id) {
  return request({
    url: `/api/v1/alerts/${id}`,
    method: 'delete'
  })
}

/**
 * 清除所有告警
 * @returns {Promise}
 */
export function clearAllAlerts() {
  return request({
    url: '/api/v1/alerts/clear',
    method: 'delete'
  })
}