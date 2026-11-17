import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { Search, Filter, ChevronDown, Loader2, MessageSquare, Users, MoreVertical } from 'lucide-react'
import { api } from '../../services/api'
import type { RoomResponse, RoomListResponse } from '../../../types/api'
import { cn } from '../../utils/cn'
import { formatDistanceToNow, format } from 'date-fns'

export default function AdminRooms() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  useState(() => {
    const timeout = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timeout)
  })

  const { data: roomsResponse, isLoading, isFetching } = useQuery({
    queryKey: ['admin-rooms', page, debouncedSearch, statusFilter],
    queryFn: () => api.getMyRooms({ page, size: 20 }), // Need admin endpoint
    placeholderData: keepPreviousData,
  })

  const rooms = roomsResponse?.rooms || []
  const total = roomsResponse?.total || 0
  const totalPages = roomsResponse?.pages || 1

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Manage Rooms</h1>
          <p className="text-muted-foreground">View and manage communication rooms</p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search rooms..."
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
            </select>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
            <p className="text-muted-foreground">Loading rooms...</p>
          </div>
        ) : rooms.length === 0 ? (
          <div className="p-12 text-center">
            <MessageSquare className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No rooms found</p>
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
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden lg:table-cell">Participants</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">Created</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rooms.map(room => (
                    <tr key={room.id} className="hover:bg-accent/50 transition-colors">
                      <td className="px-4 py-4">
                        <p className="font-medium truncate max-w-xs">{room.name}</p>
                        <p className="text-sm text-muted-foreground truncate max-w-xs mt-1">{room.description || 'No description'}</p>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {room.domain}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="text-sm text-muted-foreground">
                          {room.source_language} → {room.target_language}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden lg:table-cell">
                        <span className="text-sm text-muted-foreground">
                          {room.member_count || 0} / {room.max_participants}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                          room.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        )}>
                          {room.is_active ? (
                            <>
                              <MessageSquare className="h-3 w-3" />
                              Active
                            </>
                          ) : (
                            <>
                              <MessageSquare className="h-3 w-3" />
                              Inactive
                            </>
                          )}
                        </span>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell text-sm text-muted-foreground">
                        {format(new Date(room.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button className="p-2 rounded-lg hover:bg-accent text-muted-foreground">
                            <MoreVertical className="h-4 w-4" />
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
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} rooms
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
    </div>
  )
}