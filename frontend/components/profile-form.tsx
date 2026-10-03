'use client'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { Save } from 'lucide-react'
import { api, ApiError } from '@/services/api'
import type { Profile } from '@/types'
import { defaultProfile } from '@/lib/profile'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Spinner } from '@/components/ui/spinner'
const flags = [{ key: 'student_status', label: 'Student' }, { key: 'farmer_status', label: 'Farmer' }, { key: 'bpl_status', label: 'BPL household' }, { key: 'disability_status', label: 'Person with disability' }, { key: 'minority_status', label: 'Minority community' }, { key: 'widow_status', label: 'Widow' }, { key: 'senior_citizen_status', label: 'Senior citizen' }] as const
export function ProfileForm({ initialProfile, onSaved }: { initialProfile?: Profile | null; onSaved?: (profile: Profile) => void }) {
  const [saving, setSaving] = useState(false); const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<Profile>({ defaultValues: initialProfile ?? defaultProfile })
  useEffect(() => { if (initialProfile) reset(initialProfile) }, [initialProfile, reset])
  const submit = async (data: Profile) => { setSaving(true); try { const profile = await api.updateProfile({ ...data, age: Number(data.age), annual_income: Number(data.annual_income) }); toast.success('Eligibility profile saved.'); onSaved?.(profile) } catch (e) { toast.error(e instanceof ApiError ? e.message : 'Could not save profile.') } finally { setSaving(false) } }
  const field = (key: keyof Pick<Profile, 'full_name'|'state'|'district'|'occupation'|'education'>, label: string, placeholder: string) => <div className="space-y-2"><Label htmlFor={key}>{label}</Label><Input id={key} placeholder={placeholder} {...register(key, { required: `${label} is required` })} /><p className="text-xs text-destructive">{errors[key]?.message}</p></div>
  return <form onSubmit={handleSubmit(submit)} className="space-y-7"><div className="grid gap-5 sm:grid-cols-2">{field('full_name','Full name','Your full name')}{field('state','State / UT','e.g. Maharashtra')}{field('district','District','e.g. Pune')}{field('occupation','Occupation','e.g. Self-employed')}{field('education','Education','e.g. Undergraduate')}<div className="space-y-2"><Label htmlFor="age">Age</Label><Input id="age" type="number" min="0" max="120" {...register('age', { required: 'Age is required', min: { value: 0, message: 'Enter a valid age' } })} /><p className="text-xs text-destructive">{errors.age?.message}</p></div><div className="space-y-2"><Label htmlFor="annual_income">Annual household income (â‚¹)</Label><Input id="annual_income" type="number" min="0" {...register('annual_income', { required: 'Income is required', min: { value: 0, message: 'Income cannot be negative' } })} /><p className="text-xs text-destructive">{errors.annual_income?.message}</p></div><div className="space-y-2"><Label htmlFor="gender">Gender</Label><Select id="gender" {...register('gender')}><option value="male">Male</option><option value="female">Female</option><option value="other">Other / prefer not to say</option></Select></div><div className="space-y-2"><Label htmlFor="category">Social category</Label><Select id="category" {...register('category')}><option value="general">General</option><option value="obc">OBC</option><option value="sc">SC</option><option value="st">ST</option><option value="ews">EWS</option><option value="other">Other</option></Select></div></div><div><h3 className="mb-1 font-display text-lg font-semibold">Eligibility details</h3><p className="mb-4 text-sm text-muted-foreground">Select every statement that applies to improve your results.</p><div className="grid gap-3 sm:grid-cols-2">{flags.map(({key,label}) => <label key={key} className="flex cursor-pointer items-center gap-3 rounded-xl border p-4 hover:bg-muted/50"><Checkbox id={key} checked={watch(key)} onCheckedChange={(value) => setValue(key, value)} /><span className="text-sm font-medium">{label}</span></label>)}</div></div><Button type="submit" size="lg" disabled={saving}>{saving ? <Spinner /> : <Save />} Save eligibility profile</Button></form>
}
