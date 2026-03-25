import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { type Source, askQuestion } from '@/lib/api';
import { cn } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export default function AskPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await askQuestion(input);
      const botMessage: Message = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Sorry, I encountered an error connecting to the policy engine.';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: errorDetail },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col pt-8 pb-4">
      <div className="flex-1 overflow-y-auto px-4 space-y-6 custom-scrollbar" ref={scrollRef}>
        {messages.length === 0 && !isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center space-y-6"
          >
            <div className="w-16 h-16 premium-gradient rounded-2xl flex items-center justify-center shadow-2xl">
              <Bot className="text-white w-10 h-10" />
            </div>
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tight">How can I help you today?</h2>
              <p className="text-muted-foreground max-w-md">
                I am your company policy AI. I'll provide answers grounded strictly in your official documentation.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
              {['What is our remote work policy?', 'How many vacation days do I get?', 'Sick leave procedures', 'Travel reimbursement rules'].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="p-4 glass-card rounded-xl text-sm text-left hover:border-primary/50 transition-all hover:bg-white/5 active:scale-95"
                >
                  {q}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              className={cn(
                "flex items-start gap-4",
                msg.role === 'user' ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                msg.role === 'user' ? "bg-primary text-white" : "bg-white/10 text-muted-foreground"
              )}>
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>
              <div className="space-y-3 max-w-[80%]">
                <div className={cn(
                  "p-4 rounded-2xl text-sm leading-relaxed",
                  msg.role === 'user' 
                    ? "bg-primary/20 border border-primary/20 text-white" 
                    : "glass-card text-foreground"
                )}>
                  {msg.content}
                </div>
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src, j) => (
                      <div 
                        key={j} 
                        className="flex items-center gap-1.5 px-2 py-1 bg-white/5 border border-white/5 rounded-md text-[10px] text-muted-foreground hover:text-foreground transition-colors cursor-help group relative"
                      >
                        <Info size={10} />
                        {src.filename} (p.{src.page})
                        <div className="absolute bottom-full left-0 mb-2 w-48 p-2 bg-popover border border-white/10 rounded-md shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-[10px] whitespace-normal">
                          "{src.text}"
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="flex items-start gap-4"
          >
            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
              <Bot size={18} className="text-muted-foreground animate-pulse" />
            </div>
            <div className="glass-card p-4 rounded-2xl w-24 flex items-center justify-center">
              <Loader2 className="animate-spin text-primary" size={20} />
            </div>
          </motion.div>
        )}
      </div>

      <div className="px-4 mt-6">
        <form 
          onSubmit={handleSend}
          className="relative group focus-within:ring-2 focus-within:ring-primary/20 rounded-2xl transition-all"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about company policies..."
            className="h-16 pl-6 pr-16 bg-white/5 border-white/5 rounded-2xl focus-visible:ring-0 focus-visible:bg-white/10 transition-all text-lg"
          />
          <Button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            className="absolute right-3 top-3 w-10 h-10 premium-gradient rounded-xl shadow-lg hover:scale-105 active:scale-95 transition-all p-0"
          >
            <Send className="w-5 h-5 text-white" />
          </Button>
        </form>
        <p className="text-[10px] text-center text-muted-foreground mt-4 uppercase tracking-[0.2em]">
          Powered by Gemini 2.0 Flash Pro • Knowledge Grounded
        </p>
      </div>
    </div>
  );
}
