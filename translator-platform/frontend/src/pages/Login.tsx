import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { BookOpen, Mail, Lock, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const from = (location.state as { from?: Location })?.from?.pathname || '/dashboard'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { rememberMe: false },
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      await login(data.email, data.password, data.rememberMe)
      toast.success('Welcome back!')
      navigate(from, { replace: true })
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Invalid credentials')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/login" className="inline-flex items-center justify-center gap-2 mb-6">
            <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center">
              <BookOpen className="h-7 w-7 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold">Translator Platform</span>
          </Link>
          <h1 className="text-3xl font-bold">Sign in</h1>
          <p className="text-muted-foreground mt-2">Enter your credentials to access your account</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('email')}
                id="email"
                type="email"
                autoComplete="email"
                className={cn(
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border',
                  'bg-background text-foreground placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50',
                  errors.email && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
                placeholder="you@example.com"
              />
            </div>
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <label className="flex items-center gap-1 text-sm text-muted-foreground cursor-pointer">
                <input
                  type="checkbox"
                  {...register('rememberMe')}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                Remember me
              </label>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('password')}
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                className={cn(
                  'w-full pl-10 pr-12 py-2.5 rounded-lg border',
                  'bg-background text-foreground placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50',
                  errors.password && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              'w-full py-2.5 rounded-lg font-medium transition-colors',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        {/* Register link */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary font-medium hover:underline">
            Sign up
          </Link>
        </p>

        {/* Demo info */}
        <div className="mt-8 p-4 rounded-lg bg-accent border border-border">
          <h3 className="text-sm font-medium mb-2">Demo Credentials</h3>
          <div className="text-sm text-muted-foreground space-y-1 font-mono">
            <p>Admin: admin@translator.local / change-me-immediately</p>
            <p>User: Register a new account</p>
          </div>
        </div>
      </div>
    </div>
  )
}