import { useState } from 'react'
import { useQuery, keepPreviousData, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Filter, ChevronDown, Loader2, BookOpen, Plus, MoreVertical, Upload, Download, Edit, Trash2, FileText } from 'lucide-react'
import { api } from '../../services/api'
import type { GlossaryResponse, GlossaryListResponse, GlossaryTermResponse, GlossaryTermListResponse } from '../../../types/api'
import { cn } from '../../utils/cn'
import { formatDistanceToNow, format } from 'date-fns'
import toast from 'react-hot-toast'

export default function AdminGlossaries() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState<'all' | 'technology' | 'medical' | 'general'>('all')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedGlossary, setSelectedGlossary] = useState<GlossaryResponse | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importGlossaryId, setImportGlossaryId] = useState<string | null>(null)

  useState(() => {
    const timeout = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timeout)
  })

  const { data: glossariesResponse, isLoading, isFetching } = useQuery({
    queryKey: ['admin-glossaries', page, debouncedSearch, domainFilter],
    queryFn: () => api.getGlossaries({ page, size: 20, domain_filter: domainFilter === 'all' ? undefined : domainFilter }),
    placeholderData: keepPreviousData,
  })

  const glossaries = glossariesResponse?.glossaries || []
  const total = glossariesResponse?.total || 0
  const totalPages = glossariesResponse?.pages || 1

  // Mutations
  const createGlossaryMutation = useMutation({
    mutationFn: (data: any) => api.createGlossary(data),
    onSuccess: () => {
      toast.success('Glossary created')
      setShowCreateModal(false)
      queryClient.invalidateQueries({ queryKey: ['admin-glossaries'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to create glossary'),
  })

  const updateGlossaryMutation = useMutation({
    mutationFn: ({ glossaryId, data }: { glossaryId: string; data: any }) => api.updateGlossary(glossaryId, data),
    onSuccess: () => {
      toast.success('Glossary updated')
      setSelectedGlossary(null)
      queryClient.invalidateQueries({ queryKey: ['admin-glossaries'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to update glossary'),
  })

  const deleteGlossaryMutation = useMutation({
    mutationFn: (glossaryId: string) => api.deleteGlossary(glossaryId),
    onSuccess: () => {
      toast.success('Glossary deleted')
      queryClient.invalidateQueries({ queryKey: ['admin-glossaries'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to delete glossary'),
  })

  const importGlossaryMutation = useMutation({
    mutationFn: ({ file, data }: { file: File; data: any }) => api.importGlossary(file, data),
    onSuccess: () => {
      toast.success('Glossary imported successfully')
      setShowImportModal(false)
      setImportGlossaryId(null)
      queryClient.invalidateQueries({ queryKey: ['admin-glossaries'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to import glossary'),
  })

  const handleCreateGlossary = (data: any) => createGlossaryMutation.mutate(data)
  const handleUpdateGlossary = (data: any) => selectedGlossary && updateGlossaryMutation.mutate({ glossaryId: selectedGlossary.id, data })
  const handleDeleteGlossary = (glossaryId: string) => {
    if (confirm('Are you sure you want to delete this glossary? This will also delete all its terms.')) {
      deleteGlossaryMutation.mutate(glossaryId)
    }
  }

  const handleImport = (file: File, data: any) => {
    if (importGlossaryId) {
      importGlossaryMutation.mutate({ file, data: { ...data, glossary_id: importGlossaryId } })
    } else {
      importGlossaryMutation.mutate({ file, data })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Manage Glossaries</h1>
          <p className="text-muted-foreground">Manage domain-specific terminology for translation</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setImportGlossaryId(null); setShowImportModal(true) }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-accent"
          >
            <Upload className="h-4 w-4" />
            Import
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Glossary
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search glossaries..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <select
              value={domainFilter}
              onChange={e => { setDomainFilter(e.target.value as any); setPage(1) }}
              className="pl-10 pr-8 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary appearance-none"
            >
              <option value="all">All Domains</option>
              <option value="technology">Technology</option>
              <option value="medical">Medical</option>
              <option value="general">General</option>
            </select>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
            <p className="text-muted-foreground">Loading glossaries...</p>
          </div>
        ) : glossaries.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No glossaries found</p>
            <button onClick={() => setShowCreateModal(true)} className="mt-4 px-4 py-2 rounded-lg bg-primary text-primary-foreground">
              Create your first glossary
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Domain</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Languages</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Terms</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden lg:table-cell">Default</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Created</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {glossaries.map(glossary => (
                    <tr key={glossary.id} className="hover:bg-accent/50 transition-colors">
                      <td className="px-4 py-4">
                        <p className="font-medium truncate max-w-xs">{glossary.name}</p>
                        <p className="text-sm text-muted-foreground truncate max-w-xs mt-1">{glossary.description || 'No description'}</p>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {glossary.domain}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="text-sm text-muted-foreground">
                          {glossary.source_language} {glossary.target_language ? `→ ${glossary.target_language}` : ''}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-medium">{glossary.term_count}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                          glossary.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        )}>
                          {glossary.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden lg:table-cell">
                        {glossary.is_default && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                            Default
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell text-sm text-muted-foreground">
                        {format(new Date(glossary.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => { setSelectedGlossary(glossary); setShowImportModal(true) }}
                            className="p-2 rounded-lg hover:bg-accent text-muted-foreground"
                            title="Import Terms"
                          >
                            <Upload className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => { setSelectedGlossary(glossary); setShowCreateModal(true) }}
                            className="p-2 rounded-lg hover:bg-accent text-muted-foreground"
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteGlossary(glossary.id)}
                            className="p-2 rounded-lg hover:bg-accent text-destructive"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-border flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} glossaries
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1 || isFetching}
                    className="px-3 py-1.5 rounded-lg border border-border hover:bg-accent disabled:opacity-50"
                  >
                    <ChevronDown className="h-4 w-4 rotate-180" />
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages || isFetching}
                    className="px-3 py-1.5 rounded-lg border border-border hover:bg-accent disabled:opacity-50"
                  >
                    <ChevronDown className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create/Edit Glossary Modal */}
      {(showCreateModal || selectedGlossary) && (
        <GlossaryModal
          glossary={selectedGlossary}
          onClose={() => { setShowCreateModal(false); setSelectedGlossary(null) }}
          onSubmit={selectedGlossary ? handleUpdateGlossary : handleCreateGlossary}
          isLoading={createGlossaryMutation.isPending || updateGlossaryMutation.isPending}
        />
      )}

      {/* Import Modal */}
      {showImportModal && (
        <ImportGlossaryModal
          glossaryId={importGlossaryId}
          onClose={() => { setShowImportModal(false); setImportGlossaryId(null) }}
          onSubmit={handleImport}
          isLoading={importGlossaryMutation.isPending}
        />
      )}
    </div>
  )
}

// Glossary Modal Component
function GlossaryModal({ glossary, onClose, onSubmit, isLoading }: any) {
  const [formData, setFormData] = useState({
    name: glossary?.name || '',
    domain: glossary?.domain || 'general',
    source_language: glossary?.source_language || 'en',
    target_language: glossary?.target_language || '',
    description: glossary?.description || '',
    version: glossary?.version || '1.0',
    is_default: glossary?.is_default || false,
    is_active: glossary?.is_active !== false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-xl border border-border max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-lg font-semibold">{glossary ? 'Edit Glossary' : 'Create Glossary'}</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Domain</label>
            <select
              value={formData.domain}
              onChange={e => setFormData({ ...formData, domain: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="technology">Technology</option>
              <option value="medical">Medical</option>
              <option value="general">General</option>
            </select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Source Language</label>
              <select
                value={formData.source_language}
                onChange={e => setFormData({ ...formData, source_language: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="en">English</option>
                <option value="kn">Kannada</option>
                <option value="hi">Hindi</option>
                <option value="ml">Malayalam</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Target Language (Optional)</label>
              <select
                value={formData.target_language}
                onChange={e => setFormData({ ...formData, target_language: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">None (Multilingual)</option>
                <option value="en">English</option>
                <option value="kn">Kannada</option>
                <option value="hi">Hindi</option>
                <option value="ml">Malayalam</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description (Optional)</label>
            <textarea
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Version</label>
              <input
                type="text"
                value={formData.version}
                onChange={e => setFormData({ ...formData, version: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_default"
                checked={formData.is_default}
                onChange={e => setFormData({ ...formData, is_default: e.target.checked })}
                className="rounded border-border text-primary focus:ring-primary"
              />
              <label htmlFor="is_default" className="text-sm">Set as default for domain</label>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-border text-primary focus:ring-primary"
            />
            <label htmlFor="is_active" className="text-sm">Active</label>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-border hover:bg-accent">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {isLoading ? 'Saving...' : (glossary ? 'Save Changes' : 'Create Glossary')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Import Glossary Modal Component
function ImportGlossaryModal({ glossaryId, onClose, onSubmit, isLoading }: any) {
  const [file, setFile] = useState<File | null>(null)
  const [formData, setFormData] = useState({
    domain: 'general',
    source_language: 'en',
    target_language: '',
    name: '',
    overwrite: false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      toast.error('Please select a file')
      return
    }
    onSubmit(file, formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-xl border border-border max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-lg font-semibold">Import Glossary</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">File (CSV or JSON)</label>
            <input
              type="file"
              accept=".csv,.json"
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
            <p className="text-xs text-muted-foreground">CSV columns: original_term, alternatives, aliases, domain, source_language, target_language, case_sensitive, preserve_original, priority, active</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Domain</label>
              <select
                value={formData.domain}
                onChange={e => setFormData({ ...formData, domain: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="technology">Technology</option>
                <option value="medical">Medical</option>
                <option value="general">General</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Source Language</label>
              <select
                value={formData.source_language}
                onChange={e => setFormData({ ...formData, source_language: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="en">English</option>
                <option value="kn">Kannada</option>
                <option value="hi">Hindi</option>
                <option value="ml">Malayalam</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Target Language (Optional)</label>
            <select
              value={formData.target_language}
              onChange={e => setFormData({ ...formData, target_language: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">None (Multilingual)</option>
              <option value="en">English</option>
              <option value="kn">Kannada</option>
              <option value="hi">Hindi</option>
              <option value="ml">Malayalam</option>
              <option value="ta">Tamil</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Glossary Name (Optional - creates new if not specified)</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="overwrite"
              checked={formData.overwrite}
              onChange={e => setFormData({ ...formData, overwrite: e.target.checked })}
              className="rounded border-border text-primary focus:ring-primary"
            />
            <label htmlFor="overwrite" className="text-sm">Overwrite existing terms</label>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-border hover:bg-accent">
              Cancel
            </button>
            <button type="submit" disabled={isLoading || !file} className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {isLoading ? 'Importing...' : 'Import'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}