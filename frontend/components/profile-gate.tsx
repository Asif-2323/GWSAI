import Link from 'next/link'
import { ClipboardList } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
export function ProfileGate(){return <Card><CardContent className="flex flex-col items-start gap-4 p-8"><ClipboardList className="size-8 text-primary"/><div><h2 className="font-display text-xl font-semibold">Complete your eligibility profile first</h2><p className="mt-1 text-sm text-muted-foreground">The advisor needs your profile to give relevant scheme guidance.</p></div><Button render={<Link href="/eligibility"/>}>Complete profile</Button></CardContent></Card>}
