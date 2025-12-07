'use client'

import { useState, useRef, useEffect } from 'react'
import { sendChatMessage, ChatMessage as ChatMessageType } from '@/lib/api'
import { MessageCircle, X, Send, Bot, User } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Привет! Я AI-ассистент IntegrityOS. Спросите меня о критических дефектах, трассах или состоянии трубопроводов.',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    
    // Добавляем сообщение пользователя
    const newUserMessage: Message = { role: 'user', content: userMessage }
    setMessages((prev) => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      // Формируем историю для отправки
      const conversationHistory = messages
        .filter((msg) => msg.role !== 'assistant' || msg.content !== messages[0].content)
        .map((msg, idx, arr) => {
          if (msg.role === 'user') {
            const nextAssistant = arr[idx + 1]
            return {
              user: msg.content,
              assistant: nextAssistant?.role === 'assistant' ? nextAssistant.content : '',
            }
          }
          return null
        })
        .filter(Boolean) as Array<{ user: string; assistant: string }>

      const chatMessage: ChatMessageType = {
        message: userMessage,
        conversation_history: conversationHistory,
      }

      const response = await sendChatMessage(chatMessage)
      
      // Добавляем ответ AI
      setMessages((prev) => [...prev, { role: 'assistant', content: response.message }])
    } catch (error) {
      console.error('Ошибка при отправке сообщения:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-[1000] bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all hover:scale-110"
        aria-label="Открыть AI Assistant"
      >
        <MessageCircle className="w-6 h-6" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-[1000] w-96 h-[600px] bg-gray-900 border border-gray-800 rounded-lg shadow-2xl flex flex-col">
      {/* Заголовок */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-800/50">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">AI Assistant</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-white transition-colors"
          aria-label="Закрыть"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Сообщения */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100 border border-gray-700'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                <User className="w-5 h-5 text-gray-300" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-gray-800 text-gray-100 border border-gray-700 rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Поле ввода */}
      <div className="p-4 border-t border-gray-800 bg-gray-800/50">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Спросите о дефектах, трассах..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Пример: "Где самые критичные участки на трассе МТ-02?"
        </p>
      </div>
    </div>
  )
}


