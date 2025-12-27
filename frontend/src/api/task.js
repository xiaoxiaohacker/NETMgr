import request from '@/utils/request'

/**
 * 获取任务列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getTasks(params) {
  return request({
    url: '/api/v1/tasks/',
    method: 'get',
    params
  })
}

/**
 * 创建任务
 * @param {Object} data 任务数据
 * @returns {Promise}
 */
export function createTask(data) {
  return request({
    url: '/api/v1/tasks/',
    method: 'post',
    data
  })
}

/**
 * 获取任务详情
 * @param {number} taskId 任务ID
 * @returns {Promise}
 */
export function getTaskDetail(taskId) {
  return request({
    url: `/api/v1/tasks/${taskId}`,
    method: 'get'
  })
}

/**
 * 更新任务状态
 * @param {number} taskId 任务ID
 * @param {Object} data 更新数据
 * @returns {Promise}
 */
export function updateTask(taskId, data) {
  return request({
    url: `/api/v1/tasks/${taskId}`,
    method: 'put',
    data
  })
}

/**
 * 删除任务
 * @param {number} taskId 任务ID
 * @returns {Promise}
 */
export function deleteTask(taskId) {
  return request({
    url: `/api/v1/tasks/${taskId}`,
    method: 'delete'
  })
}

/**
 * 执行任务
 * @param {number} taskId 任务ID
 * @returns {Promise}
 */
export function executeTask(taskId) {
  return request({
    url: `/api/v1/tasks/${taskId}/execute`,
    method: 'post'
  })
}

/**
 * 取消任务
 * @param {number} taskId 任务ID
 * @returns {Promise}
 */
export function cancelTask(taskId) {
  return request({
    url: `/api/v1/tasks/${taskId}`,
    method: 'put',
    data: {
      status: 'cancelled'
    }
  })
}