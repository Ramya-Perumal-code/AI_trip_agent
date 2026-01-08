import { useState } from 'react';
import { apiService } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AdditionalInfo.css';

const AdditionalInfo = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clean up tool call syntax from the response
  const cleanResponse = (text: string): string => {
    if (!text) return text;
    
    // Remove tool call tags like <search_rag>...</search_rag> or <duckduckgo_search>...</duckduckgo_search>
    let cleaned = text.replace(/<search_rag>[\s\S]*?<\/search_rag>/gi, '');
    cleaned = cleaned.replace(/<duckduckgo_search>[\s\S]*?<\/duckduckgo_search>/gi, '');
    // Remove standalone tool call tags
    cleaned = cleaned.replace(/<\/?(search_rag|duckduckgo_search)[^>]*>/gi, '');
    // Clean up extra whitespace
    cleaned = cleaned.replace(/\n\s*\n\s*\n+/g, '\n\n');
    return cleaned.trim();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiService.gatherAdditionalInfo({ query });
      if (data && data.info) {
        // Clean up any tool call syntax from the response
        const cleanedData = {
          ...data,
          info: cleanResponse(data.info)
        };
        setResult(cleanedData);
      } else {
        setError('Received empty response from server. Please try again.');
      }
    } catch (err: any) {
      console.error('Error gathering additional info:', err);
      let errorMessage = 'Failed to gather information';
      
      if (err.response) {
        // Server responded with error status
        errorMessage = err.response.data?.detail || 
                      err.response.data?.message || 
                      `Server error: ${err.response.status} ${err.response.statusText}`;
      } else if (err.request) {
        // Request was made but no response received
        errorMessage = 'No response from server. Please check if the API server is running.';
      } else {
        // Something else happened
        errorMessage = err.message || errorMessage;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="additional-info">
      <h2>Gather Additional Information</h2>
      <p className="description">
        Research travel destinations, attractions, and trip planning information.
        The agent will search both local knowledge base and the web.
      </p>

      <form onSubmit={handleSubmit} className="info-form">
        <div className="form-group">
          <label htmlFor="query">Travel Query</label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., about San Diego Zoo Day Pass"
            disabled={loading}
            className="query-input"
          />
        </div>
        <button type="submit" disabled={loading || !query.trim()} className="submit-button">
          {loading ? 'Gathering Information...' : 'Search'}
        </button>
      </form>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Searching RAG database and web for information...</p>
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
            <h3>Gathered Information</h3>
            {result.success && (
              <span className="success-badge">Success</span>
            )}
          </div>
          {result.query && (
            <div className="query-display">
              <strong>Query:</strong> {result.query}
            </div>
          )}
          {result.info ? (
            <div className="info-content">
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
                  {result.info}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="info-content">
              <p className="text-muted-foreground italic">No information was returned. Please try a different query.</p>
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

export default AdditionalInfo;





