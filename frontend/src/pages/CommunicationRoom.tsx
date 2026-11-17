import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Mic, MicOff, Loader2, X, Copy, Check, MessageSquare, Users, Globe, Shield, ArrowLeft, MoreVertical, Download } from 'lucide-react'
import { api } from '../services/api'
import type { RoomDetailResponse, RoomMemberResponse, MessageResponse, WSMessageMessage, WSUserJoined, WSUserLeft, WSTyping, LanguageCode, ConversationDomain } from '../types/api'
import { cn } from '../utils/cn'
import { formatDistanceToNow, format } from 'date-fns'
import toast from 'react-hot-toast'

const languageNames: Record<LanguageCode, string> = {
  en: 'English',
  kn: 'Kannada',
  hi: 'Hindi',
  ml: 'Malayalam',
  ta: 'Tamil',
}

const domainNames: Record<ConversationDomain, string> = {
  technology: 'Technology',
  medical: 'Medical',
  general: 'General',
}

export default function CommunicationRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [messageText, setMessageText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showOriginal, setShowOriginal] = useState(true)
  const [typingUsers, setTypingUsers] = useState<string[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()

  // Fetch room details
  const { data: room, isLoading: roomLoading, refetch: refetchRoom } = useQuery({
    queryKey: ['room', roomId],
    queryFn: () => api.getRoom(roomId!),
    enabled: !!roomId,
  })

  // Fetch messages
  const { data: messagesResponse, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', roomId],
    queryFn: () => api.getRoomMessages(roomId!), // We'll need to add this endpoint
    enabled: !!roomId,
  })

  // For now, use a mock messages array since we don't have the endpoint yet
  const messages: MessageResponse[] = messagesResponse?.messages || []

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (text: string) => api.sendMessage(roomId!, text), // Need to add this
    onSuccess: () => {
      setMessageText('')
      queryClient.invalidateQueries({ queryKey: ['messages', roomId] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to send message')
    },
  })

  // WebSocket connection
  useEffect(() => {
    if (!roomId) return

    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/connect?token=${token}`
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      setConnected(true)
      setReconnecting(false)
      // Join room
      websocket.send(JSON.stringify({ type: 'join_room', room_id: roomId }))
    }

    websocket.onclose = () => {
      setConnected(false)
      // Attempt reconnect
      setReconnecting(true)
      setTimeout(() => {
        // Reconnect logic would go here
      }, 3000)
    }

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleWSMessage(message)
      } catch (e) {
        console.error('Failed to parse WS message:', e)
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [roomId, navigate])

  const handleWSMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connected':
        console.log('WS connected:', message.connection_id)
        break
      case 'join_room_response':
        if (!message.success) {
          toast.error('Failed to join room')
          navigate('/dashboard')
        }
        break
      case 'message':
        // Add message to cache
        queryClient.setQueryData(['messages', roomId], (old: any) => {
          if (!old) return { messages: [message.message] }
          return { messages: [...old.messages, message.message] }
        })
        break
      case 'user_joined':
        toast.success(`${message.user_name} joined the room`)
        break
      case 'user_left':
        toast(`${message.user_name} left the room`)
        break
      case 'typing':
        if (message.is_typing) {
          setTypingUsers(prev => [...new Set([...prev, message.user_name])])
        } else {
          setTypingUsers(prev => prev.filter(name => name !== message.user_name))
        }
        break
      case 'error':
        toast.error(message.message)
        break
    }
  }, [roomId, queryClient, navigate])

  const sendMessage = () => {
    if (!messageText.trim() || !ws || ws.readyState !== WebSocket.OPEN) return

    ws.send(JSON.stringify({
      type: 'send_message',
      room_id: roomId,
      text: messageText.trim(),
    }))

    setMessageText('')
    setIsTyping(false)
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current)
  }

  const handleTyping = () => {
    setIsTyping(true)
    ws?.send(JSON.stringify({ type: 'typing', room_id: roomId, is_typing: true }))

    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current)
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false)
      ws?.send(JSON.stringify({ type: 'typing', room_id: roomId, is_typing: false }))
    }, 1000)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return format(date, 'HH:mm')
  }

  if (roomLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!room) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <MessageSquare className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">Room not found</h3>
          <button onClick={() => navigate('/dashboard')} className="mt-4 px-4 py-2 rounded-lg bg-primary text-primary-foreground">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-200px)] flex-col rounded-xl border border-border bg-card overflow-hidden">
      {/* Room Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 border-b border-border">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="p-2 rounded-lg hover:bg-accent transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold">{room.name}</h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                {domainNames[room.domain]}
              </span>
              <span>•</span>
              <Globe className="h-3.5 w-3.5" />
              <span>{languageNames[room.source_language]} → {languageNames[room.target_language]}</span>
              <span>•</span>
              <Users className="h-3.5 w-3.5" />
              <span>{room.member_count} participants</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className={cn(
            'flex items-center gap-2 px-3 py-1 rounded-full text-sm',
            connected ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
          )}>
            <span className={cn('connection-indicator', connected ? 'connected' : 'connecting')} />
            {connected ? 'Connected' : reconnecting ? 'Reconnecting...' : 'Disconnected'}
          </div>

          {/* Toggle original/translated */}
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              showOriginal
                ? 'bg-primary text-primary-foreground'
                : 'border border-border hover:bg-accent'
            )}
          >
            {showOriginal ? 'Show Original' : 'Show Translated'}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={messagesEndRef}>
        {messagesLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <MessageSquare className="h-16 w-16 mb-4 opacity-50" />
            <p>No messages yet</p>
            <p className="text-sm">Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              showOriginal={showOriginal}
              currentUserId={localStorage.getItem('user_id') || ''}
              copyToClipboard={copyToClipboard}
              formatMessageTime={formatMessageTime}
            />
          ))
        )}

        {/* Typing indicator */}
        {typingUsers.length > 0 && (
          <div className="typing-indicator mx-4 mb-2">
            <span></span><span></span><span></span>
            <span className="ml-2">
              {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-border">
        <div className="flex items-end gap-2">
          <textarea
            value={messageText}
            onChange={e => { setMessageText(e.target.value); handleTyping() }}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
            rows={1}
            className="flex-1 min-h-[44px] max-h-32 px-4 py-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            disabled={!connected}
          />
          <button
            onClick={sendMessage}
            disabled={!messageText.trim() || !connected || sendMessageMutation.isPending}
            className={cn(
              'p-3 rounded-lg transition-colors flex-shrink-0',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-1 text-right">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

// Message Bubble Component
interface MessageBubbleProps {
  message: MessageResponse
  showOriginal: boolean
  currentUserId: string
  copyToClipboard: (text: string) => void
  formatMessageTime: (timestamp: string) => string
}

function MessageBubble({
  message,
  showOriginal,
  currentUserId,
  copyToClipboard,
  formatMessageTime,
}: MessageBubbleProps) {
  const isOwn = message.sender_id === currentUserId
  const text = showOriginal ? message.original_text : (message.translated_text || message.original_text)
  const lang = showOriginal ? message.original_language : (message.translated_language || message.original_language)

  return (
    <div className={cn('flex gap-3', isOwn && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-medium">
        {message.sender_id.charAt(0).toUpperCase()}
      </div>

      <div className={cn('flex-1 max-w-[70%]', isOwn && 'text-right')}>
        <div className={cn(
          'inline-block px-4 py-2 rounded-2xl',
          isOwn
            ? 'bg-primary text-primary-foreground rounded-br-md'
            : 'bg-secondary text-secondary-foreground rounded-bl-md'
        )}>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-xs font-medium">{isOwn ? 'You' : message.sender_id}</span>
            <span className="text-xs text-muted-foreground/70">{formatMessageTime(message.created_at)}</span>
          </div>
          <p className="whitespace-pre-wrap">{text}</p>

          {/* Protected terms indicator */}
          {message.glossary_applied && message.protected_terms && Object.keys(message.protected_terms).length > 0 && (
            <div className="mt-2 pt-2 border-t border-border/50">
              <div className="flex flex-wrap gap-1">
                {Object.entries(message.protected_terms).map(([placeholder, original]) => (
                  <span key={placeholder} className="protected-term text-xs">
                    {original}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 mt-2">
            <span className="language-badge bg-background/50 px-2 py-0.5">
              {lang}
            </span>
            <button
              onClick={() => copyToClipboard(text)}
              className="p-1 rounded hover:bg-background/50 text-muted-foreground/50 hover:text-foreground"
              title="Copy"
            >
              <Copy className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}