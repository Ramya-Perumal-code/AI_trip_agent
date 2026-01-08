import { useState } from 'react';
import { apiService } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './FinalResponse.css';

const FinalResponse = () => {
  const [content, setContent] = useState('');
  const [userQuery, setUserQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Please enter content to synthesize');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiService.generateFinalResponse({
        content,
        user_query: userQuery || undefined,
      });
      setResult(data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || 'Failed to generate response'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="final-response">
      <h2>Generate Final Response</h2>
      <p className="description">
        Synthesize gathered information into a clear, comprehensive, and user-friendly response.
      </p>

      <form onSubmit={handleSubmit} className="response-form">
        <div className="form-group">
          <label htmlFor="content">Content to Synthesize *</label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter the gathered information to synthesize..."
            disabled={loading}
            rows={6}
            className="content-textarea"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="userQuery">Original User Query (Optional)</label>
          <input
            id="userQuery"
            type="text"
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            placeholder="e.g., Tell me about the Las Vegas Strip"
            disabled={loading}
            className="query-input"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="submit-button"
        >
          {loading ? 'Generating Response...' : 'Generate Response'}
        </button>
      </form>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Synthesizing information into final response...</p>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="result">
          <div className="result-header">
            <h3>Final Response</h3>
            {result.success && (
              <span className="success-badge">Success</span>
            )}
          </div>
          {result.response && (
            <div className="response-content">
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
                  {result.response}
                </ReactMarkdown>
              </div>
            </div>
          )}
          {result.message && (
            <div className="result-message">{result.message}</div>
          )}
        </div>
      )}
    </div>
  );
};

export default FinalResponse;





