import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Glossary {
  id: string
  name: string
  department: string | null
  description: string | null
  entry_count: number
  created_at: string
  updated_at: string
}

interface GlossaryEntry {
  id: number
  glossary_id: string
  source_term: string
  target_term: string
  context_note: string | null
  created_at: string
}

interface GlossaryListResponse {
  glossaries: Glossary[]
}

interface GlossaryDetailResponse {
  glossary: Glossary
  entries: GlossaryEntry[]
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function CreateGlossaryForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [department, setDepartment] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (body: { name: string; department?: string; description?: string }) =>
      api.post<Glossary>('/api/glossary/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossaries'] })
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    setError(null)
    createMutation.mutate({
      name: name.trim(),
      department: department.trim() || undefined,
      description: description.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
      <h3 className="font-medium text-gray-900">Create Glossary</h3>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. Cardiology Terms"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
        <input
          type="text"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. Cardiology"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
          placeholder="Optional description"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {createMutation.isPending ? 'Creating...' : 'Create'}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-100"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

function EntryRow({
  entry,
  onEdit,
  onDelete,
}: {
  entry: GlossaryEntry
  onEdit: (entry: GlossaryEntry) => void
  onDelete: (entry: GlossaryEntry) => void
}) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-2 px-3 text-sm text-gray-900">{entry.source_term}</td>
      <td className="py-2 px-3 text-sm text-gray-900">{entry.target_term}</td>
      <td className="py-2 px-3 text-sm text-gray-500">{entry.context_note || '-'}</td>
      <td className="py-2 px-3 text-right">
        <button
          onClick={() => onEdit(entry)}
          className="text-xs text-blue-600 hover:text-blue-800 mr-3"
        >
          Edit
        </button>
        <button
          onClick={() => onDelete(entry)}
          className="text-xs text-red-600 hover:text-red-800"
        >
          Delete
        </button>
      </td>
    </tr>
  )
}

function EntriesTable({
  glossaryId,
  entries,
  onEntriesChanged,
}: {
  glossaryId: string
  entries: GlossaryEntry[]
  onEntriesChanged: () => void
}) {
  const queryClient = useQueryClient()
  const [editingEntry, setEditingEntry] = useState<GlossaryEntry | null>(null)
  const [editSource, setEditSource] = useState('')
  const [editTarget, setEditTarget] = useState('')
  const [editContext, setEditContext] = useState('')

  // New entry form state
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSource, setNewSource] = useState('')
  const [newTarget, setNewTarget] = useState('')
  const [newContext, setNewContext] = useState('')

  // Import state
  const [importError, setImportError] = useState<string | null>(null)

  const addEntryMutation = useMutation({
    mutationFn: (body: { source_term: string; target_term: string; context_note?: string }) =>
      api.post(`/api/glossary/${glossaryId}/entries`, body),
    onSuccess: () => {
      setShowAddForm(false)
      setNewSource('')
      setNewTarget('')
      setNewContext('')
      queryClient.invalidateQueries({ queryKey: ['glossary', glossaryId] })
      onEntriesChanged()
    },
    onError: (err: Error) => setImportError(err.message),
  })

  const updateEntryMutation = useMutation({
    mutationFn: ({
      entryId,
      body,
    }: {
      entryId: number
      body: { source_term?: string; target_term?: string; context_note?: string }
    }) => api.put(`/api/glossary/${glossaryId}/entries/${entryId}`, body),
    onSuccess: () => {
      setEditingEntry(null)
      queryClient.invalidateQueries({ queryKey: ['glossary', glossaryId] })
      onEntriesChanged()
    },
    onError: (err: Error) => setImportError(err.message),
  })

  const deleteEntryMutation = useMutation({
    mutationFn: (entryId: number) => api.del(`/api/glossary/${glossaryId}/entries/${entryId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossary', glossaryId] })
      onEntriesChanged()
    },
    onError: (err: Error) => setImportError(err.message),
  })

  const importMutation = useMutation({
    mutationFn: (formData: FormData) => api.upload(`/api/glossary/${glossaryId}/import`, formData),
    onSuccess: () => {
      setImportError(null)
      queryClient.invalidateQueries({ queryKey: ['glossary', glossaryId] })
      onEntriesChanged()
    },
    onError: (err: Error) => setImportError(err.message),
  })

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    importMutation.mutate(formData)
    // Reset input so same file can be re-imported
    e.target.value = ''
  }

  const handleEditStart = (entry: GlossaryEntry) => {
    setEditingEntry(entry)
    setEditSource(entry.source_term)
    setEditTarget(entry.target_term)
    setEditContext(entry.context_note || '')
  }

  const handleEditSave = () => {
    if (!editingEntry) return
    updateEntryMutation.mutate({
      entryId: editingEntry.id,
      body: {
        source_term: editSource.trim(),
        target_term: editTarget.trim(),
        context_note: editContext.trim() || undefined,
      },
    })
  }

  const handleDeleteConfirm = (entry: GlossaryEntry) => {
    if (window.confirm(`Delete entry "${entry.source_term}"?`)) {
      deleteEntryMutation.mutate(entry.id)
    }
  }

  return (
    <div className="mt-3 space-y-3">
      {importError && (
        <p className="text-red-600 text-sm">{importError}</p>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          {showAddForm ? 'Cancel' : '+ Add Entry'}
        </button>
        <label className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded-md hover:bg-purple-700 cursor-pointer inline-block">
          {importMutation.isPending ? 'Importing...' : 'Import CSV/Excel'}
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={handleImportFile}
            className="hidden"
          />
        </label>
      </div>

      {/* Add entry form */}
      {showAddForm && (
        <div className="flex gap-2 items-end flex-wrap p-3 border border-gray-200 rounded-md bg-gray-50">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Source</label>
            <input
              type="text"
              value={newSource}
              onChange={(e) => setNewSource(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-sm"
              placeholder="source term"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Target</label>
            <input
              type="text"
              value={newTarget}
              onChange={(e) => setNewTarget(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-sm"
              placeholder="target term"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Context</label>
            <input
              type="text"
              value={newContext}
              onChange={(e) => setNewContext(e.target.value)}
              className="px-2 py-1.5 border border-gray-300 rounded text-sm"
              placeholder="optional"
            />
          </div>
          <button
            onClick={() =>
              addEntryMutation.mutate({
                source_term: newSource.trim(),
                target_term: newTarget.trim(),
                context_note: newContext.trim() || undefined,
              })
            }
            disabled={addEntryMutation.isPending || !newSource.trim() || !newTarget.trim()}
            className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {addEntryMutation.isPending ? 'Adding...' : 'Add'}
          </button>
        </div>
      )}

      {/* Entries table */}
      {entries.length > 0 ? (
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-2 px-3 text-xs font-medium text-gray-500 uppercase">Source</th>
              <th className="py-2 px-3 text-xs font-medium text-gray-500 uppercase">Target</th>
              <th className="py-2 px-3 text-xs font-medium text-gray-500 uppercase">Context</th>
              <th className="py-2 px-3 text-xs font-medium text-gray-500 uppercase text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) =>
              editingEntry?.id === entry.id ? (
                <tr key={entry.id} className="border-b border-gray-100 bg-yellow-50">
                  <td className="py-2 px-3">
                    <input
                      type="text"
                      value={editSource}
                      onChange={(e) => setEditSource(e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </td>
                  <td className="py-2 px-3">
                    <input
                      type="text"
                      value={editTarget}
                      onChange={(e) => setEditTarget(e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </td>
                  <td className="py-2 px-3">
                    <input
                      type="text"
                      value={editContext}
                      onChange={(e) => setEditContext(e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </td>
                  <td className="py-2 px-3 text-right">
                    <button
                      onClick={handleEditSave}
                      disabled={updateEntryMutation.isPending}
                      className="text-xs text-blue-600 hover:text-blue-800 mr-3"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingEntry(null)}
                      className="text-xs text-gray-600 hover:text-gray-800"
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ) : (
                <EntryRow
                  key={entry.id}
                  entry={entry}
                  onEdit={handleEditStart}
                  onDelete={handleDeleteConfirm}
                />
              )
            )}
          </tbody>
        </table>
      ) : (
        <p className="text-sm text-gray-500 italic">No entries yet. Add entries or import a file.</p>
      )}
    </div>
  )
}

function GlossaryCard({
  glossary,
  onDelete,
}: {
  glossary: Glossary
  onDelete: (id: string) => void
}) {
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState(false)

  const { data: detailData, isLoading } = useQuery({
    queryKey: ['glossary', glossary.id],
    queryFn: () => api.get<GlossaryDetailResponse>(`/api/glossary/${glossary.id}`),
    enabled: expanded,
  })

  const handleEntriesChanged = () => {
    queryClient.invalidateQueries({ queryKey: ['glossaries'] })
  }

  return (
    <div className="border border-gray-200 rounded-lg bg-white">
      {/* Header row */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => setExpanded(!expanded)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setExpanded(!expanded)
          }
        }}
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50"
      >
        <div className="flex items-center gap-4 min-w-0">
          <span className="text-gray-400 transition-transform duration-200" style={{ transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
            &#9654;
          </span>
          <div className="min-w-0">
            <span className="font-medium text-gray-900">{glossary.name}</span>
            {glossary.department && (
              <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                {glossary.department}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{glossary.entry_count} entries</span>
          <span className="text-xs">{formatDate(glossary.updated_at)}</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(glossary.id)
            }}
            className="text-xs text-red-600 hover:text-red-800"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-200 px-4 py-3">
          {glossary.description && (
            <p className="text-sm text-gray-600 mb-2">{glossary.description}</p>
          )}
          {isLoading ? (
            <p className="text-sm text-gray-500">Loading entries...</p>
          ) : detailData ? (
            <EntriesTable
              glossaryId={glossary.id}
              entries={detailData.entries}
              onEntriesChanged={handleEntriesChanged}
            />
          ) : null}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function GlossaryPage() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['glossaries'],
    queryFn: () => api.get<GlossaryListResponse>('/api/glossary/'),
  })

  const deleteGlossaryMutation = useMutation({
    mutationFn: (id: string) => api.del(`/api/glossary/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossaries'] })
    },
  })

  const handleDeleteGlossary = (id: string) => {
    const glossary = data?.glossaries.find((g) => g.id === id)
    const name = glossary?.name || 'this glossary'
    if (window.confirm(`Delete glossary "${name}" and all its entries? This cannot be undone.`)) {
      deleteGlossaryMutation.mutate(id)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Glossaries</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : '+ Create Glossary'}
        </button>
      </div>

      {showCreateForm && (
        <CreateGlossaryForm onClose={() => setShowCreateForm(false)} />
      )}

      {isLoading && <p className="text-gray-500">Loading glossaries...</p>}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          Failed to load glossaries: {error.message}
        </div>
      )}

      {data && data.glossaries.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No glossaries yet</p>
          <p className="text-sm">Create your first glossary to start managing translation terms.</p>
        </div>
      )}

      {data && data.glossaries.length > 0 && (
        <div className="space-y-2">
          {data.glossaries.map((glossary) => (
            <GlossaryCard
              key={glossary.id}
              glossary={glossary}
              onDelete={handleDeleteGlossary}
            />
          ))}
        </div>
      )}
    </div>
  )
}
