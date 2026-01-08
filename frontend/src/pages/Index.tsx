import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { apiService } from "@/services/api";

interface Message {
  id: string;
  text: string;
  isAssistant: boolean;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hello! I'm your Trip Agent assistant. Ask me about travel destinations, attractions, and trip planning!",
      isAssistant: true,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isAssistant: false,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call final-response endpoint directly
      // FinalResponseAgent will gather information using tools if needed
      const response = await apiService.generateFinalResponse({
        content: "", // Empty content - agent will gather info using tools
        user_query: text, // Required when content is empty
      });

      if (!response || !response.response) {
        throw new Error("Failed to generate response");
      }

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        isAssistant: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error("Error:", error);
      let errorMessage = "Sorry, I encountered an error while processing your request. Please try again.";
      
      if (error.response) {
        errorMessage = error.response.data?.detail || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: errorMessage,
        isAssistant: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="border-b border-border bg-white/80 backdrop-blur-md sticky top-0 z-10 shadow-sm"
      >
        <div className="max-w-4xl mx-auto px-6 py-5">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            🌍 Trip Agent
          </h1>
          <p className="text-sm text-slate-600 mt-1.5">
            Intelligent Travel Information Assistant
          </p>
        </div>
      </motion.header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              message={message.text}
              isAssistant={message.isAssistant}
              index={index}
            />
          ))}
          {isLoading && (
            <div className="flex gap-3 mb-6 items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-md bg-white text-slate-800 border border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm text-slate-600">Gathering information and generating response...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="border-t border-slate-200 bg-white/90 backdrop-blur-md sticky bottom-0 shadow-lg"
      >
        <div className="max-w-4xl mx-auto px-6 py-6">
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      </motion.div>
    </div>
  );
};

export default Index;
