import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api } from '../services/api'
import toast from 'react-hot-toast'
import { ArrowLeft, Loader2, TicketPlus } from 'lucide-react'
import Link from 'react-router-dom'
import { cn } from '../utils/cn'

const ticketSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().min(1, 'Description is required'),
  priority: z.enum(['low', 'normal', 'high', 'urgent']),
  domain: z.enum(['technology', 'medical', 'general']),
  source_language: z.enum(['en', 'kn', 'hi', 'ml', 'ta']),
  target_language: z.enum(['en', 'kn', 'hi', 'ml', 'ta']),
}).refine(data => data.source_language !== data.target_language, {
  message: 'Source and target languages must be different',
  path: ['target_language'],
})

type TicketForm = z.infer<typeof ticketSchema>

const priorities = [
  { value: 'low', label: 'Low', description: 'Non-urgent, flexible timeline' },
  { value: 'normal', label: 'Normal', description: 'Standard priority' },
  { value: 'high', label: 'High', description: 'Important, needs attention soon' },
  { value: 'urgent', label: 'Urgent', description: 'Critical, immediate attention required' },
]

const domains = [
  { value: 'technology', label: 'Technology', description: 'Software, programming, AI, IT' },
  { value: 'medical', label: 'Medical', description: 'Healthcare, clinical, medical terms' },
  { value: 'general', label: 'General', description: 'Everyday conversation, non-technical' },
]

const languages = [
  { code: 'en', name: 'English' },
  { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'ml', name: 'Malayalam (മലയാളം)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
]

export default function CreateTicket() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TicketForm>({
    resolver: zodResolver(ticketSchema),
    defaultValues: {
      priority: 'normal',
      domain: 'general',
      source_language: 'en',
      target_language: 'kn',
    },
  })

  const sourceLanguage = watch('source_language')
  const targetLanguage = watch('target_language')

  // Auto-swap target language if it matches source
  const handleSourceLanguageChange = (value: string) => {
    setValue('source_language', value)
    if (value === targetLanguage) {
      // Find a different language
      const otherLang = languages.find(l => l.code !== value)
      if (otherLang) setValue('target_language', otherLang.code)
    }
  }

  const onSubmit = async (data: TicketForm) => {
    setIsLoading(true)
    try {
      const ticket = await api.createTicket(data)
      toast.success('Ticket created successfully!')
      navigate(`/tickets/history`)
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create ticket')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/dashboard" className="p-2 rounded-lg hover:bg-accent transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Create Communication Ticket</h1>
          <p className="text-muted-foreground">Request a new multilingual communication session</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-6">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <TicketPlus className="h-5 w-5" />
            Basic Information
          </h2>

          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">Title</label>
            <input
              {...register('title')}
              id="title"
              type="text"
              className={cn(
                'w-full px-4 py-2.5 rounded-lg border',
                'bg-background focus:outline-none focus:ring-2 focus:ring-primary',
                errors.title && 'border-destructive focus:ring-destructive'
              )}
              placeholder="Brief description of the communication need"
              disabled={isLoading}
            />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">Description</label>
            <textarea
              {...register('description')}
              id="description"
              rows={4}
              className={cn(
                'w-full px-4 py-2.5 rounded-lg border',
                'bg-background focus:outline-none focus:ring-2 focus:ring-primary',
                errors.description && 'border-destructive focus:ring-destructive'
              )}
              placeholder="Detailed description of what you need to communicate..."
              disabled={isLoading}
            />
            {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
          </div>
        </div>

        {/* Language Settings */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-6">
          <h2 className="text-lg font-semibold">Language Settings</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Source Language</label>
              <select
                {...register('source_language')}
                onChange={e => handleSourceLanguageChange(e.target.value)}
                className={cn(
                  'w-full px-4 py-2.5 rounded-lg border',
                  'bg-background focus:outline-none focus:ring-2 focus:ring-primary',
                  errors.source_language && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Target Language</label>
              <select
                {...register('target_language')}
                className={cn(
                  'w-full px-4 py-2.5 rounded-lg border',
                  'bg-background focus:outline-none focus:ring-2 focus:ring-primary',
                  errors.target_language && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
              >
                {languages
                  .filter(lang => lang.code !== sourceLanguage)
                  .map(lang => (
                    <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
              </select>
              {errors.target_language && (
                <p className="text-sm text-destructive">{errors.target_language.message}</p>
              )}
            </div>
          </div>

          {/* Language swap indicator */}
          <div className="flex items-center justify-center text-sm text-muted-foreground">
            <span className="px-2 py-1 bg-accent rounded-full">
              {languages.find(l => l.code === sourceLanguage)?.name} → {languages.find(l => l.code === targetLanguage)?.name}
            </span>
          </div>
        </div>

        {/* Domain & Priority */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-6">
          <h2 className="text-lg font-semibold">Domain & Priority</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Conversation Domain</label>
              <div className="space-y-2">
                {domains.map(domain => (
                  <label
                    key={domain.value}
                    className={cn(
                      'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors',
                      'hover:bg-accent',
                      watch('domain') === domain.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border'
                    )}
                  >
                    <input
                      type="radio"
                      {...register('domain')}
                      value={domain.value}
                      className="mt-1 h-4 w-4 text-primary border-border focus:ring-primary"
                    />
                    <div>
                      <p className="font-medium">{domain.label}</p>
                      <p className="text-sm text-muted-foreground">{domain.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <div className="space-y-2">
                {priorities.map(priority => (
                  <label
                    key={priority.value}
                    className={cn(
                      'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors',
                      'hover:bg-accent',
                      watch('priority') === priority.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border'
                    )}
                  >
                    <input
                      type="radio"
                      {...register('priority')}
                      value={priority.value}
                      className="mt-1 h-4 w-4 text-primary border-border focus:ring-primary"
                    />
                    <div>
                      <p className="font-medium">{priority.label}</p>
                      <p className="text-sm text-muted-foreground">{priority.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-4">
          <Link
            to="/dashboard"
            className="flex-1 px-4 py-2.5 rounded-lg border border-border text-center font-medium hover:bg-accent transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              'flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Ticket'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}