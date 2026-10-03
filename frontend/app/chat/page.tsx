'use client'

import { FormEvent, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, Send, UserRound } from 'lucide-react'
import { toast } from 'sonner'
import { api, ApiError } from '@/services/api'
import type { ChatMessage } from '@/types'
import { ProtectedPage } from '@/components/protected-page'
import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Textarea } from '@/components/ui/textarea'

const starters = [
  'What documents are required for welfare schemes?',
  'What schemes are available for farmers?',
  'What if my income changes?',
  'What scholarships are available?',
]

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  const send = async (event?: FormEvent, question = value) => {
    event?.preventDefault()
    const text = question.trim()
    if (!text || loading) return

    const history = messages
    setMessages([...history, { role: 'user', content: text }])
    setValue('')
    setLoading(true)

    try {
      const response = await api.chat(text, history)
      const sources = response.sources.length ? `\n\nSources: ${response.sources.join(' Â· ')}` : ''
      setMessages((current) => [...current, { role: 'assistant', content: response.answer + sources }])
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Could not get an answer.')
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: "I couldn't find this information in the available government scheme documents." },
      ])
    } finally {
      setLoading(false)
      ref.current?.focus()
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        title="Ask the scheme advisor"
        description="Answers are grounded in the available government scheme documents. If no information is available, the advisor will say so."
      />
      <Card className="flex min-h-[560px] flex-col">
        <CardContent className="flex flex-1 flex-col p-0">
          <div className="flex-1 space-y-5 overflow-y-auto p-5 sm:p-7">
            {!messages.length && (
              <div className="py-12 text-center">
                <span className="mx-auto grid size-12 place-items-center rounded-full bg-primary/10 text-primary"><Bot /></span>
                <h2 className="mt-4 font-display text-xl font-semibold">What would you like to know?</h2>
                <p className="mt-2 text-sm text-muted-foreground">Try one of these questions to get started.</p>
                <div className="mx-auto mt-6 flex max-w-xl flex-wrap justify-center gap-2">
                  {starters.map((question) => (
                    <Button key={question} variant="outline" size="sm" onClick={() => send(undefined, question)}>
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((message, index) => {
              const isAssistant = message.role === 'assistant'

              return (
                <div key={index} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}>
                  <span className={`grid size-8 shrink-0 place-items-center rounded-full ${isAssistant ? 'bg-primary text-primary-foreground' : 'order-2 bg-muted'}`}>
                    {isAssistant ? <Bot className="size-4" /> : <UserRound className="size-4" />}
                  </span>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                      isAssistant ? 'rounded-tl-sm bg-muted text-foreground' : 'order-1 rounded-tr-sm bg-primary text-primary-foreground'
                    }`}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, ...props }) => (
                          <a {...props} className="underline underline-offset-2" target="_blank" rel="noreferrer" />
                        ),
                        p: ({ children }) => <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>,
                        ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
                        ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
                        li: ({ children }) => <li className="leading-6">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        code: ({ children, className, ...props }) => (
                          <code className={`${className ?? ''} rounded bg-black/5 px-1 py-0.5 text-[0.85em]`} {...props}>
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => <pre className="mb-2 overflow-x-auto rounded-md bg-black/10 p-3 text-xs">{children}</pre>,
                        h1: ({ children }) => <h1 className="mb-2 text-base font-semibold">{children}</h1>,
                        h2: ({ children }) => <h2 className="mb-2 text-sm font-semibold">{children}</h2>,
                        h3: ({ children }) => <h3 className="mb-2 text-sm font-semibold">{children}</h3>,
                        blockquote: ({ children }) => <blockquote className="mb-2 border-l-2 border-border pl-3 text-muted-foreground">{children}</blockquote>,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
              )
            })}
            {loading && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Spinner /> Searching the scheme documentsâ€¦</div>}
          </div>
          <form onSubmit={send} className="border-t p-4">
            <div className="flex gap-3">
              <Textarea ref={ref} value={value} onChange={(event) => setValue(event.target.value)} placeholder="Ask about documents, eligibility, schemes, or application processâ€¦" className="min-h-11 resize-none" rows={1} />
              <Button type="submit" size="icon-lg" disabled={!value.trim() || loading} aria-label="Send message"><Send /></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </ProtectedPage>
  )
}
