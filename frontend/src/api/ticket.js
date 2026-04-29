import request from './request'

export function getTickets(params) {
  return request({
    url: '/tickets',
    method: 'get',
    params
  })
}

export function getTicket(id) {
  return request({
    url: `/tickets/${id}`,
    method: 'get'
  })
}

export function createTicket(data) {
  return request({
    url: '/tickets',
    method: 'post',
    data
  })
}

export function updateTicket(id, data) {
  return request({
    url: `/tickets/${id}`,
    method: 'put',
    data
  })
}

export function submitEvidence(id, data) {
  return request({
    url: `/tickets/${id}/evidence`,
    method: 'post',
    data
  })
}

export function sendMessage(id, data) {
  return request({
    url: `/tickets/${id}/messages`,
    method: 'post',
    data
  })
}

export function getMessages(id, params) {
  return request({
    url: `/tickets/${id}/messages`,
    method: 'get',
    params
  })
}

export function escalate(id, data) {
  return request({
    url: `/tickets/${id}/escalate`,
    method: 'post',
    data
  })
}

export function arbitrate(id, data) {
  return request({
    url: `/tickets/${id}/arbitrate`,
    method: 'post',
    data
  })
}

export function getSlaMonitoring(params) {
  return request({
    url: '/tickets/sla-monitor',
    method: 'get',
    params
  })
}

export function getStatistics(params) {
  return request({
    url: '/tickets/statistics',
    method: 'get',
    params
  })
}

export function getSimilarCases(id) {
  return request({
    url: `/tickets/${id}/similar-cases`,
    method: 'get'
  })
}

export function uploadEvidence(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/evidence/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function analyzeImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/analysis/image',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function analyzeText(data) {
  return request({
    url: '/analysis/text',
    method: 'post',
    data
  })
}
