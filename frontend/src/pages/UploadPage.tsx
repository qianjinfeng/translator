import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

interface Config {
  source_languages: string
  target_languages: string
  output_mode: string
  ai_provider: string
  rag_enabled: boolean
  image_translation_enabled: boolean
  glossary_id: string | null
}

interface Glossary {
  id: string
  name: string
}

interface GlossaryResponse {
  glossaries: Glossary[]
}

interface UploadResponse {
  task_id: string
  status: string
  progress_pct: number
}

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50 MB

const defaultConfig: Config = {
  source_languages: 'en',
  target_languages: 'zh',
  output_mode: 'bilingual',
  ai_provider: 'ollama',
  rag_enabled: false,
  image_translation_enabled: false,
  glossary_id: null,
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [config, setConfig] = useState<Config>(defaultConfig)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: glossaryData } = useQuery({
    queryKey: ['glossaries'],
    queryFn: () => api.get<GlossaryResponse>('/api/glossary/'),
    staleTime: 60_000,
  })

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null
    if (f && f.size > MAX_FILE_SIZE) {
      setError(`File size exceeds 50 MB limit (${(f.size / 1024 / 1024).toFixed(1)} MB)`)
      setFile(null)
      return
    }
    setFile(f)
    setError(null)
  }, [])

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }
    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('config', JSON.stringify(config))

      const task = await api.upload<UploadResponse>('/api/translation/upload', formData)
      navigate(`/translate/${task.task_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const glossaries = glossaryData?.glossaries ?? []

  return (
    <div className="max-w-2xl mx-auto">
      {/* File upload */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">1. Upload Document</h2>
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            file ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          {file ? (
            <div>
              <p className="text-lg font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {(file.size / 1024 / 1024).toFixed(1)} MB
              </p>
              <button
                onClick={() => setFile(null)}
                className="mt-3 text-sm text-blue-600 hover:text-blue-800"
              >
                Change file
              </button>
            </div>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">Drag & drop or click to select</p>
              <p className="text-xs text-gray-400">Accepted formats: DOCX, PDF (max 50 MB)</p>
              <input
                type="file"
                accept=".docx,.pdf"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                style={{ position: 'absolute', inset: 0 }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">2. Configure</h2>

        <div className="grid grid-cols-2 gap-4">
          {/* Source language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source Language</label>
            <select
              value={config.source_languages}
              onChange={(e) => setConfig({ ...config, source_languages: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="en">English</option>
              <option value="en+de">English + German</option>
            </select>
          </div>

          {/* Target language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Language</label>
            <select
              value={config.target_languages}
              onChange={(e) => setConfig({ ...config, target_languages: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="zh">Chinese</option>
              <option value="en+zh">English + Chinese</option>
            </select>
          </div>

          {/* Output mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Output Mode</label>
            <select
              value={config.output_mode}
              onChange={(e) => setConfig({ ...config, output_mode: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="bilingual">Bilingual</option>
              <option value="standalone">Standalone Translation</option>
            </select>
          </div>

          {/* AI Provider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">AI Provider</label>
            <select
              value={config.ai_provider}
              onChange={(e) => setConfig({ ...config, ai_provider: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="ollama">Ollama (Qwen3 14B)</option>
              <option value="anthropic">Claude (Anthropic)</option>
              <option value="deepl">DeepL</option>
            </select>
          </div>

          {/* Glossary */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Glossary</label>
            <select
              value={config.glossary_id ?? ''}
              onChange={(e) => setConfig({ ...config, glossary_id: e.target.value || null })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">None</option>
              {glossaries.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="mt-6 space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.rag_enabled}
              onChange={(e) => setConfig({ ...config, rag_enabled: e.target.checked })}
              className="rounded border-gray-300"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">RAG Translation Memory</span>
              <p className="text-xs text-gray-500">Use prior translation pairs to improve consistency</p>
            </div>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.image_translation_enabled}
              onChange={(e) => setConfig({ ...config, image_translation_enabled: e.target.checked })}
              className="rounded border-gray-300"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">Image Translation</span>
              <p className="text-xs text-gray-500">Extract and translate text in document images</p>
            </div>
          </label>
        </div>
      </div>

      {/* Action */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || uploading}
        className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? 'Uploading...' : 'Start Translation'}
      </button>
    </div>
  )
}
