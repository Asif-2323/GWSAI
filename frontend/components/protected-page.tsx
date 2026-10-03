'use client'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuth } from '@/context/auth-context'
import { AppShell } from '@/components/app-shell'
import { Spinner } from '@/components/ui/spinner'
export function ProtectedPage({ children }: { children: React.ReactNode }) { const { user, loading } = useAuth(); const router = useRouter(); useEffect(() => { if (!loading && !user) router.replace('/login') }, [loading, user, router]); if (loading || !user) return <div className="grid min-h-screen place-items-center"><Spinner className="size-7 text-primary" /></div>; return <AppShell>{children}</AppShell> }
