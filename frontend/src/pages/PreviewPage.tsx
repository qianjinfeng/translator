import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api/client'

interface Segment {
  segment_index: number
  source_text: string
  translated_text: string | null
  segment_type: string
}

interface TaskDetail {
  id: string
  status: string
  original_filename: string
  segments: Segment[]
}

interface TaskResponse {
  task: TaskDetail
}

const SEGMENT_TYPE_BADGES: Record<string, { label: string; className: string }> = {
  paragraph: { label: 'Paragraph', className: 'bg-blue-100 text-blue-700' },
  table_cell: { label: 'Table Cell', className: 'bg-purple-100 text-purple-700' },
  header: { label: 'Header', className: 'bg-green-100 text-green-700' },
  footer: { label: 'Footer', className: 'bg-gray-100 text-gray-700' },
  footnote: { label: 'Footnote', className: 'bg-amber-100 text-amber-700' },
  image: { label: 'Image', className: 'bg-pink-100 text-pink-700' },
}

function getSegmentTypeBadge(type: string): { label: string; className: string } {
  return SEGMENT_TYPE_BADGES[type] ?? { label: type, className: 'bg-gray-100 text-gray-600' }
}

export default function PreviewPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [editMode, setEditMode] = useState(false)
  const [editedSegments, setEditedSegments] = useState<Record<number, string>>({})

  const { data: task, isLoading } = useQuery({
    queryKey: ['task-detail', taskId],
    queryFn: async () => {
      const res = await api.get<TaskResponse>(`/api/translation/tasks/${taskId}`)
      return res.task
    },
  })

  const handleDownload = () => {
    if (taskId) {
      window.open(`/api/translation/tasks/${taskId}/download`, '_blank')
    }
  }

  if (isLoading || !task) {
    return (
      <div className="max-w-4xl mx-auto text-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Preview: {task.original_filename}</h2>
          <p className="text-sm text-gray-500">{task.segments.length} segments</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setEditMode(!editMode)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              editMode
                ? 'bg-gray-200 text-gray-700'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {editMode ? 'Done Editing' : 'Edit'}
          </button>
          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Download DOCX
          </button>
        </div>
      </div>

      {/* Segments */}
      <div className="space-y-4">
        {task.segments.map((seg) => {
          const badge = getSegmentTypeBadge(seg.segment_type)
          return (
            <div
              key={seg.segment_index}
              className="bg-white rounded-lg border border-gray-200 p-4 grid grid-cols-2 gap-4"
            >
              <div>
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${badge.className}`}
                >
                  {badge.label}
                </span>
                <p className="text-sm text-gray-900 mt-1 whitespace-pre-wrap">{seg.source_text}</p>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase font-medium">Translation</span>
                {editMode ? (
                  <textarea
                    value={editedSegments[seg.segment_index] ?? seg.translated_text ?? ''}
                    onChange={(e) =>
                      setEditedSegments({
                        ...editedSegments,
                        [seg.segment_index]: e.target.value,
                      })
                    }
                    className="w-full border border-gray-300 rounded mt-1 px-2 py-1 text-sm min-h-[60px]"
                  />
                ) : (
                  <p
                    className={`text-sm mt-1 whitespace-pre-wrap ${
                      seg.translated_text
                        ? 'text-blue-800'
                        : 'text-gray-400 italic'
                    }`}
                  >
                    {seg.translated_text ?? '(no translation)'}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom actions */}
      <div className="flex gap-3 mt-8 justify-center">
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          New Translation
        </button>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Download DOCX
        </button>
      </div>
    </div>
  )
}
