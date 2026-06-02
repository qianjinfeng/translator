const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

interface ApiError {
  detail: string
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  // For FormData, let the browser set Content-Type with multipart boundary
  const isFormData = options?.body instanceof FormData

  const headers: Record<string, string> = {}
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      ...headers,
      ...(options?.headers as Record<string, string> | undefined),
    },
  })

  if (!res.ok) {
    const err: ApiError = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body?: unknown) =>
    request<T>(url, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(url: string, body?: unknown) =>
    request<T>(url, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  del: <T>(url: string) =>
    request<T>(url, { method: 'DELETE' }),
  upload: <T>(url: string, formData: FormData) =>
    request<T>(url, { method: 'POST', body: formData }),
}

// Health check
export async function checkHealth(): Promise<{ status: string }> {
  return api.get('/api/health')
}
