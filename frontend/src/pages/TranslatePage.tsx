import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

interface TaskStatus {
  id: string
  status: string
  original_filename: string
  progress_pct: number
  total_segments: number
  translated_segments: number
  error_message: string | null
}

interface TaskResponse {
  task: TaskStatus
}

export default function TranslatePage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()

  const { data: task, isLoading } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const res = await api.get<TaskResponse>(`/api/translation/tasks/${taskId}`)
      return res.task
    },
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 1000
      if (['completed', 'failed'].includes(data.status)) return false
      return 1000 // poll every second while translating
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    )
  }

  const isDone = task?.status === 'completed' || task?.status === 'translated'
  const isFailed = task?.status === 'failed'
  const isTranslating = task && !isDone && !isFailed

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">3. Translating</h2>
        <p className="text-sm text-gray-500 mb-6">{task?.original_filename}</p>

        {/* Status and progress */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>
              {isDone && 'Completed'}
              {isTranslating && 'Translating...'}
              {isFailed && 'Failed'}
            </span>
            <span>
              {task ? `${task.translated_segments}/${task.total_segments}` : ''}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`rounded-full h-3 transition-all duration-500 ${
                isFailed ? 'bg-red-500' : 'bg-blue-600'
              }`}
              style={{ width: `${task?.progress_pct || 0}%` }}
            />
          </div>

          {/* Segment-by-segment progress label */}
          {isTranslating && task && task.total_segments > 0 && (
            <p className="text-center text-sm text-gray-500 mt-2">
              Translating segment {Math.min(task.translated_segments + 1, task.total_segments)} of {task.total_segments}
            </p>
          )}
          {!isTranslating && (
            <p className="text-center text-sm text-gray-500 mt-2">
              {(task?.progress_pct || 0).toFixed(0)}%
            </p>
          )}
        </div>

        {/* Error */}
        {isFailed && task?.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-sm font-medium text-red-800">Translation failed</p>
            <p className="text-sm text-red-600 mt-1">{task.error_message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-6">
          {isDone && (
            <button
              onClick={() => navigate(`/preview/${taskId}`)}
              className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Preview & Download
            </button>
          )}
          {isFailed && (
            <button
              onClick={() => navigate('/')}
              className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          )}
          <button
            onClick={() => navigate('/')}
            className={`flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors ${
              isDone || isFailed ? '' : 'bg-white'
            }`}
          >
            {isDone || isFailed ? 'New Translation' : 'Back to Home'}
          </button>
        </div>
      </div>
    </div>
  )
}
