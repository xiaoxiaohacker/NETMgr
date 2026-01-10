import request from '@/utils/request'

/**
 * 获取备份任务列表
 * @param {Object} params 查询参数 { skip, limit }
 * @returns {Promise}
 */
export function getBackupTasks(params) {
  return request({
    url: '/api/v1/backup-tasks/',
    method: 'get',
    params
  })
}

/**
 * 获取备份统计信息
 * @returns {Promise}
 */
export function getBackupStatistics() {
  return request({
    url: '/api/v1/backup-tasks/statistics',
    method: 'get'
  })
}

/**
 * 创建备份任务（支持单个或多个设备）
 * @param {Object} data 任务数据
 * @returns {Promise}
 */
export function createBackupTask(data) {
  return request({
    url: '/api/v1/backup-tasks/',
    method: 'post',
    data
  })
}

/**
 * 批量执行备份任务
 * @param {Object} data 设备ID列表
 * @returns {Promise}
 */
export function executeBatchBackup(data) {
  return request({
    url: '/api/v1/backup-tasks/batch-execute',
    method: 'post',
    data
  })
}

/**
 * 获取所有配置备份
 * @param {Object} params 查询参数 { page, size }
 * @returns {Promise}
 */
export function getAllConfigBackups(params) {
  return request({
    url: '/api/v1/config-backup/backup-tasks/all',
    method: 'get',
    params
  })
}

/**
 * 删除配置备份
 * @param {Number} id 配置备份ID
 * @returns {Promise}
 */
export function deleteConfigBackup(id) {
  return request({
    // url: `/api/v1/backup-tasks/${id}`,
    url: `/api/v1/config-backup/${id}`,
    method: 'delete'
  })
}

/**
 * 获取配置备份内容
 * @param {Number} id 配置备份ID
 * @returns {Promise}
 */
export function downloadConfigBackup(id) {
  return request({
    url: `/api/v1/config-backup/${id}/download`,
    method: 'get'
  })
}