import { useState } from 'react'
import { useQuery, keepPreviousData, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Filter, ChevronDown, Loader2, Users, MoreVertical, Shield, UserPlus, Edit, Trash2 } from 'lucide-react'
import { api } from '../../services/api'
import type { UserResponse, UserListResponse, RoleResponse } from '../../../types/api'
import { cn } from '../../utils/cn'
import { formatDistanceToNow, format } from 'date-fns'
import toast from 'react-hot-toast'

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  suspended: 'bg-red-100 text-red-800',
  pending_verification: 'bg-yellow-100 text-yellow-800',
}

export default function AdminUsers() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'suspended'>('all')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState<UserResponse | null>(null)

  useState(() => {
    const timeout = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timeout)
  })

  const { data: usersResponse, isLoading, isFetching } = useQuery({
    queryKey: ['admin-users', page, debouncedSearch, statusFilter],
    queryFn: () => api.getUsers({ page, size: 20, search: debouncedSearch }),
    placeholderData: keepPreviousData,
  })

  const { data: rolesResponse } = useQuery({
    queryKey: ['admin-roles'],
    queryFn: () => api.getRoles(),
  })

  const users = usersResponse?.users || []
  const roles = rolesResponse || []
  const total = usersResponse?.total || 0
  const totalPages = usersResponse?.pages || 1

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: (data: any) => api.createUser(data),
    onSuccess: () => {
      toast.success('User created')
      setShowCreateModal(false)
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to create user'),
  })

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) => api.updateUser(userId, data),
    onSuccess: () => {
      toast.success('User updated')
      setShowEditModal(null)
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to update user'),
  })

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => api.deleteUser(userId),
    onSuccess: () => {
      toast.success('User deactivated')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (error: any) => toast.error(error.response?.data?.message || 'Failed to delete user'),
  })

  const handleCreateUser = (data: any) => {
    createUserMutation.mutate(data)
  }

  const handleUpdateUser = (data: any) => {
    if (showEditModal) {
      updateUserMutation.mutate({ userId: showEditModal.id, data })
    }
  }

  const handleDeleteUser = (userId: string) => {
    if (confirm('Are you sure you want to deactivate this user?')) {
      deleteUserMutation.mutate(userId)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Manage Users</h1>
          <p className="text-muted-foreground">Manage user accounts and roles</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <UserPlus className="h-4 w-4" />
          Add User
        </button>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search users..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <select
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value as any); setPage(1) }}
              className="pl-10 pr-8 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary appearance-none"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
            <p className="text-muted-foreground">Loading users...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No users found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">User</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Roles</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Language</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Last Login</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden lg:table-cell">Created</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {users.map(user => (
                    <tr key={user.id} className="hover:bg-accent/50 transition-colors">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                            {user.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.full_name}</p>
                            <p className="text-sm text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <div className="flex flex-wrap gap-1">
                          {user.roles.map(role => (
                            <span key={role.id} className={cn(
                              'px-2 py-0.5 rounded-full text-xs font-medium',
                              role.name === 'admin' ? 'bg-purple-100 text-purple-800' :
                              role.name === 'room_agent' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            )}>
                              {role.display_name}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="text-sm text-muted-foreground">{user.preferred_language}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={cn('px-2 py-1 rounded-full text-xs font-medium', statusColors[user.status] || 'bg-gray-100 text-gray-800')}>
                          {user.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell text-sm text-muted-foreground">
                        {user.last_login ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true }) : 'Never'}
                      </td>
                      <td className="px-4 py-4 hidden lg:table-cell text-sm text-muted-foreground">
                        {format(new Date(user.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setShowEditModal(user)}
                            className="p-2 rounded-lg hover:bg-accent text-muted-foreground"
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="p-2 rounded-lg hover:bg-accent text-destructive"
                            title="Deactivate"
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
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} users
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

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateUser}
          roles={roles}
          isLoading={createUserMutation.isPending}
        />
      )}

      {/* Edit User Modal */}
      {showEditModal && (
        <EditUserModal
          user={showEditModal}
          onClose={() => setShowEditModal(null)}
          onSubmit={handleUpdateUser}
          roles={roles}
          isLoading={updateUserMutation.isPending}
        />
      )}
    </div>
  )
}

// Create User Modal Component
function CreateUserModal({ onClose, onSubmit, roles, isLoading }: any) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    preferred_language: 'en',
    role_names: [] as string[],
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-xl border border-border max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-lg font-semibold">Create User</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
              minLength={8}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Full Name</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={e => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Phone (Optional)</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={e => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Preferred Language</label>
            <select
              value={formData.preferred_language}
              onChange={e => setFormData({ ...formData, preferred_language: e.target.value })}
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
            <label className="text-sm font-medium">Roles</label>
            <div className="space-y-2">
              {roles.map((role: any) => (
                <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.role_names.includes(role.name)}
                    onChange={e => setFormData({
                      ...formData,
                      role_names: e.target.checked
                        ? [...formData.role_names, role.name]
                        : formData.role_names.filter((r: string) => r !== role.name)
                    })}
                    className="rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-sm">{role.display_name}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-border hover:bg-accent">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {isLoading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Edit User Modal Component
function EditUserModal({ user, onClose, onSubmit, roles, isLoading }: any) {
  const [formData, setFormData] = useState({
    full_name: user.full_name,
    phone: user.phone || '',
    preferred_language: user.preferred_language,
    status: user.status,
    is_superuser: user.is_superuser,
    roles: user.roles.map((r: any) => r.name),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-card rounded-xl border border-border max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-lg font-semibold">Edit User</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Full Name</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={e => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={e => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Preferred Language</label>
            <select
              value={formData.preferred_language}
              onChange={e => setFormData({ ...formData, preferred_language: e.target.value })}
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
            <label className="text-sm font-medium">Status</label>
            <select
              value={formData.status}
              onChange={e => setFormData({ ...formData, status: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Superuser</label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_superuser}
                onChange={e => setFormData({ ...formData, is_superuser: e.target.checked })}
                className="rounded border-border text-primary focus:ring-primary"
              />
              <span className="text-sm">Grant superuser access</span>
            </label>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Roles</label>
            <div className="space-y-2">
              {roles.map((role: any) => (
                <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.roles.includes(role.name)}
                    onChange={e => setFormData({
                      ...formData,
                      roles: e.target.checked
                        ? [...formData.roles, role.name]
                        : formData.roles.filter((r: string) => r !== role.name)
                    })}
                    className="rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-sm">{role.display_name}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-border hover:bg-accent">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}