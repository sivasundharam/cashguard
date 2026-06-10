import axios from 'axios'

const api = axios.create({ baseURL: '' })

export const getLatestForecast = () => api.get('/api/forecast/latest')
export const runForecast = () => api.post('/api/forecast/run')
export const getOverdueInvoices = () => api.get('/api/invoices/overdue')
export const getCases = () => api.get('/api/cases')
export const getPendingApprovals = () => api.get('/api/approvals/pending')
export const runPipeline = () => api.post('/api/pipeline/run')
export const approveCase = (caseId) => api.post(`/api/approvals/${caseId}/approve`)
export const rejectCase = (caseId) => api.post(`/api/approvals/${caseId}/reject`)
export const getHealth = () => api.get('/api/health')
