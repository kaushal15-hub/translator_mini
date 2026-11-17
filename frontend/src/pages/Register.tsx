import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { BookOpen, Mail, Lock, User, Phone, Globe, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  full_name: z.string().min(1, 'Full name is required'),
  phone: z.string().optional(),
  preferred_language: z.enum(['en', 'kn', 'hi', 'ml', 'ta']),
}).refine(data => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
})

type RegisterForm = z.infer<typeof registerSchema>

const languages = [
  { code: 'en', name: 'English' },
  { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'ml', name: 'Malayalam (മലയാളം)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
]

export default function Register() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { preferred_language: 'en' },
  })

  const password = watch('password')

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        phone: data.phone,
        preferred_language: data.preferred_language,
      })
      toast.success('Account created successfully!')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  const getPasswordStrength = (pwd: string) => {
    let strength = 0
    if (pwd.length >= 8) strength++
    if (/[A-Z]/.test(pwd)) strength++
    if (/[a-z]/.test(pwd)) strength++
    if (/[0-9]/.test(pwd)) strength++
    if (/[^A-Za-z0-9]/.test(pwd)) strength++
    return strength
  }

  const strength = getPasswordStrength(password)
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
  const strengthColors = [
    'bg-destructive',
    'bg-orange-500',
    'bg-yellow-500',
    'bg-lime-500',
    'bg-green-500',
  ]

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/login" className="inline-flex items-center justify-center gap-2 mb-6">
            <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center">
              <BookOpen className="h-7 w-7 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold">Translator Platform</span>
          </Link>
          <h1 className="text-3xl font-bold">Create Account</h1>
          <p className="text-muted-foreground mt-2">Join the multilingual communication platform</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="full_name" className="text-sm font-medium">
              Full Name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('full_name')}
                id="full_name"
                type="text"
                autoComplete="name"
                className={cn(
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border',
                  'bg-background text-foreground placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50',
                  errors.full_name && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
                placeholder="John Doe"
              />
            </div>
            {errors.full_name && (
              <p className="text-sm text-destructive">{errors.full_name.message}</p>
            )}
          </div>

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
            <label htmlFor="phone" className="text-sm font-medium">
              Phone (Optional)
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('phone')}
                id="phone"
                type="tel"
                autoComplete="tel"
                className={cn(
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border',
                  'bg-background text-foreground placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50'
                )}
                disabled={isLoading}
                placeholder="+1 (555) 000-0000"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="preferred_language" className="text-sm font-medium">
              Preferred Language
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <select
                {...register('preferred_language')}
                id="preferred_language"
                className={cn(
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border appearance-none',
                  'bg-background text-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50'
                )}
                disabled={isLoading}
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('password')}
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
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

            {/* Password strength meter */}
            {password && (
              <div className="space-y-1">
                <div className="h-1.5 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full transition-all duration-300',
                      strengthColors[strength - 1] || 'bg-transparent'
                    )}
                    style={{ width: `${(strength / 5) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Strength: {strengthLabels[strength - 1] || 'Very Weak'}
                </p>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="text-sm font-medium">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                {...register('confirmPassword')}
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                className={cn(
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border',
                  'bg-background text-foreground placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                  'disabled:opacity-50',
                  errors.confirmPassword && 'border-destructive focus:ring-destructive'
                )}
                disabled={isLoading}
                placeholder="••••••••"
              />
            </div>
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
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
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Login link */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}