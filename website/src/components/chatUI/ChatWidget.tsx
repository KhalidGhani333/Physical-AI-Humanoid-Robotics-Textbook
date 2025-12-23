import React, { useState, useEffect, useRef } from 'react';
import styles from './chatWidget.module.css';

// Define TypeScript interfaces based on the data model
interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
  status?: 'sent' | 'pending' | 'error';
}

interface ChatWidgetState {
  isOpen: boolean;
  messages: ChatMessage[];
  inputText: string;
  isLoading: boolean;
  selectedText: string | null;
  showContextBadge: boolean;
  error: string | null;
  sessionId: string;
}

const ChatWidget: React.FC = () => {
  // Generate a unique session ID or retrieve from localStorage for continuity
  const generateSessionId = (): string => {
    const existingSessionId = localStorage.getItem('chatWidgetSessionId');
    if (existingSessionId) {
      return existingSessionId;
    }
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('chatWidgetSessionId', newSessionId);
    return newSessionId;
  };

  const [state, setState] = useState<ChatWidgetState>({
    isOpen: false,
    messages: [], // In a real app, you might load previous messages from localStorage
    inputText: '',
    isLoading: false,
    selectedText: null,
    showContextBadge: false,
    error: null,
    sessionId: generateSessionId(),
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Function to get selected text using the utility
  const getSelectedText = (): string | null => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim() !== '') {
      return selection.toString().trim();
    }
    return null;
  };

  // Check for selected text when component mounts and on selection change
  useEffect(() => {
    const handleSelectionChange = () => {
      const selectedText = getSelectedText();
      setState(prev => ({
        ...prev,
        selectedText,
        showContextBadge: !!selectedText
      }));
    };

    document.addEventListener('selectionchange', handleSelectionChange);

    // Initial check
    handleSelectionChange();

    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  // Toggle chat window visibility
  const toggleChatWindow = () => {
    setState(prev => ({
      ...prev,
      isOpen: !prev.isOpen
    }));
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setState(prev => ({
      ...prev,
      inputText: e.target.value,
      error: null
    }));
  };

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!state.inputText.trim()) return;

    // Input validation
    if (state.inputText.trim().length > 1000) {
      setState(prev => ({
        ...prev,
        error: 'Message is too long. Please keep it under 1000 characters.'
      }));
      return;
    }

    // Add user message to the chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content: state.inputText,
      timestamp: new Date(),
      status: 'pending'
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      inputText: '',
      isLoading: true,
      error: null
    }));

    try {
      // Call the backend API to get response
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout to allow for processing

      // Use a safer approach for environment variable access in React
      // The REACT_APP_API_BASE_URL is embedded at build time, but we need to handle cases where it's undefined
      const API_BASE_URL = typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE_URL
        ? process.env.REACT_APP_API_BASE_URL
        : 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: state.inputText,
          selected_text: state.selectedText || undefined,  // Updated field name to match backend
          session_token: state.sessionId,  // Updated field name to match backend
          mode: "full_content"  // Added required field for backend
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // Handle different error statuses
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait before sending another message.');
        } else {
          throw new Error(`API request failed with status ${response.status}`);
        }
      }

      const data = await response.json();

      // Add bot response to the chat
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        content: data.response || 'Sorry, I could not process your request.',
        timestamp: new Date(),
        status: 'sent'
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, botMessage],
        isLoading: false,
        selectedText: null, // Clear selected text after sending
        showContextBadge: false,
        sessionId: data.session_token || prev.sessionId // Update session ID if returned by backend
      }));
    } catch (error) {
      console.error('Error sending message:', error);

      // Check if it's a timeout error
      if (error instanceof Error && error.name === 'AbortError') {
        // Add timeout error message to the chat
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          content: 'Request timed out. Please try again.',
          timestamp: new Date(),
          status: 'error'
        };

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, errorMessage],
          isLoading: false,
          error: 'Request timed out'
        }));
      } else {
        // Add error message to the chat with more specific details
        let errorMessageContent = 'Sorry, I encountered an error. Please try again.';

        if (error instanceof TypeError && error.message.includes('fetch')) {
          errorMessageContent = 'Unable to connect to the server. Please make sure the backend is running on http://localhost:8000.';
        } else if (error instanceof Error) {
          if (error.message.includes('429')) {
            errorMessageContent = error.message;
          } else if (error.message.includes('Failed to fetch')) {
            errorMessageContent = 'Connection failed. Please check if the backend server is running.';
          } else {
            errorMessageContent = `Error: ${error.message}`;
          }
        }

        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          content: errorMessageContent,
          timestamp: new Date(),
          status: 'error'
        };

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, errorMessage],
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unknown error occurred'
        }));
      }
    }
  };

  // Handle key press (Enter to send, Shift+Enter for new line)
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Close chat window when clicking outside
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      setState(prev => ({ ...prev, isOpen: false }));
    }
  };

  // Close chat window with ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && state.isOpen) {
        setState(prev => ({ ...prev, isOpen: false }));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state.isOpen]);

  return (
    <div className={styles.chatWidgetContainer} role="complementary" aria-label="AI Chat Assistant">
      {/* Floating Action Button */}
      <button
        className={styles.fabButton}
        onClick={toggleChatWindow}
        aria-label={state.isOpen ? "Close chat" : "Open chat"}
        aria-expanded={state.isOpen}
      >
        💬
      </button>

      {/* Chat Window */}
      {state.isOpen && (
        <div
          className={styles.chatWindow + ' ' + styles.open}
          onClick={handleBackdropClick}
          role="dialog"
          aria-modal="true"
          aria-label="Chat interface"
          aria-describedby={state.showContextBadge ? "context-indicator" : undefined}
        >
          <div className={styles.chatHeader} role="banner">
            <h3>AI Assistant</h3>
            <button
              className={styles.closeButton}
              onClick={() => setState(prev => ({ ...prev, isOpen: false }))}
              aria-label="Close chat"
              aria-controls="chat-window"
            >
              ×
            </button>
          </div>

          {/* Context Indicator */}
          {state.showContextBadge && (
            <div
              className={styles.contextIndicator}
              id="context-indicator"
              role="status"
              aria-live="polite"
            >
              <span aria-hidden="true">📎</span>
              <span>Context found</span>
            </div>
          )}

          {/* Messages Container */}
          <div
            className={styles.messagesContainer}
            role="log"
            aria-live="polite"
            aria-label="Chat messages"
          >
            {state.messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${
                  message.sender === 'user'
                    ? styles.userMessage
                    : styles.botMessage
                }`}
                role="listitem"
                aria-label={`${message.sender === 'user' ? 'User' : 'Assistant'} message: ${message.content}`}
              >
                {message.content}
              </div>
            ))}

            {state.isLoading && (
              <div
                className={styles.loadingIndicator}
                role="status"
                aria-live="polite"
              >
                <span aria-hidden="true">🤖</span>
                <span>Thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          {/* Input Area */}
          <div className={styles.inputArea} role="form" aria-label="Message input">
            <textarea
              ref={inputRef}
              className={styles.messageInput}
              value={state.inputText}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              aria-label="Type your message"
              aria-required="true"
              rows={1}
              disabled={state.isLoading}
            />
            <button
              className={styles.sendButton}
              onClick={handleSendMessage}
              disabled={!state.inputText.trim() || state.isLoading}
              aria-label="Send message"
              aria-disabled={!state.inputText.trim() || state.isLoading}
            >
              <span aria-hidden="true">➤</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWidget;