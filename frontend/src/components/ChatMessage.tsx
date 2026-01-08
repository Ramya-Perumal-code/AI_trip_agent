import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  message: string;
  isAssistant: boolean;
  index: number;
}

export const ChatMessage = ({ message, isAssistant, index }: ChatMessageProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        ease: [0.4, 0, 0.2, 1],
      }}
      className={cn(
        "flex gap-3 mb-6 items-start",
        isAssistant ? "justify-start" : "justify-end"
      )}
    >
      {isAssistant && (
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, delay: index * 0.1 + 0.1 }}
          className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md"
        >
          <Bot className="w-5 h-5 text-white" />
        </motion.div>
      )}
      
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3, delay: index * 0.1 + 0.15 }}
        className={cn(
          "max-w-[75%] px-5 py-3.5 rounded-2xl shadow-md",
          isAssistant
            ? "bg-white text-slate-800 border border-slate-200"
            : "bg-gradient-to-br from-blue-500 to-indigo-600 text-white"
        )}
      >
        {isAssistant ? (
          <div className="text-[15px] leading-relaxed break-words markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                h1: ({ children }) => <h1 className="text-2xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-semibold mb-2 mt-3 first:mt-0">{children}</h3>,
                h4: ({ children }) => <h4 className="text-base font-semibold mb-2 mt-3 first:mt-0">{children}</h4>,
                ul: ({ children }) => <ul className="list-disc list-outside mb-3 ml-4 space-y-1.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-outside mb-3 ml-4 space-y-1.5">{children}</ol>,
                li: ({ children }) => <li className="pl-1">{children}</li>,
                code: ({ children, className, ...props }) => {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !className || !match;
                  return isInline ? (
                    <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-primary" {...props}>
                      {children}
                    </code>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => {
                  const child = children as any;
                  if (child?.props?.className) {
                    return (
                      <pre className="bg-muted p-4 rounded-lg overflow-x-auto mb-3 border border-border">
                        {children}
                      </pre>
                    );
                  }
                  return (
                    <pre className="bg-muted p-4 rounded-lg overflow-x-auto mb-3 border border-border">
                      {children}
                    </pre>
                  );
                },
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-primary/50 pl-4 italic my-3 text-muted-foreground">
                    {children}
                  </blockquote>
                ),
                a: ({ href, children }) => (
                  <a 
                    href={href} 
                    className="text-primary hover:underline font-medium" 
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    {children}
                  </a>
                ),
                hr: () => <hr className="my-4 border-border" />,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full border-collapse border border-border">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
                th: ({ children }) => <th className="border border-border px-4 py-2 text-left font-semibold">{children}</th>,
                td: ({ children }) => <td className="border border-border px-4 py-2">{children}</td>,
              }}
            >
              {message}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap break-words">
            {message}
          </p>
        )}
      </motion.div>

      {!isAssistant && (
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, delay: index * 0.1 + 0.1 }}
          className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center shadow-sm"
        >
          <User className="w-5 h-5 text-slate-700" />
        </motion.div>
      )}
    </motion.div>
  );
};
