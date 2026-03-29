import React, { useState } from 'react';
import { chatWithBot } from '../../services/api'; // Import the API service

interface ChatInterfaceProps {
  onClose: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'bot'; text: string; sources?: string[] }[]>([
    { sender: 'bot', text: 'Hello! How can I help you with Physical AI & Humanoid Robotics today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null); // New state for error message

  const handleSendMessage = async () => {
    if (input.trim() && !isLoading) {
      const userMessage = input.trim();
      setMessages((prevMessages) => [...prevMessages, { sender: 'user', text: userMessage }]);
      setInput('');
      setIsLoading(true);
      setErrorMessage(null); // Clear previous error messages

      try {
        const response = await chatWithBot(userMessage);
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: 'bot', text: response.answer, sources: response.sources }
        ]);
      } catch (error: any) { // Explicitly type error as 'any' or 'Error'
        console.error('Chat API error:', error);
        const displayMessage = error.message || 'Sorry, I am having trouble connecting right now. Please try again later.';
        setErrorMessage(displayMessage); // Set the error message
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: 'bot', text: displayMessage } // Display error in chat as well
        ]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: '80px',
      right: '20px',
      zIndex: 999,
      backgroundColor: 'white',
      border: '1px solid #ccc',
      borderRadius: '10px',
      width: '300px',
      height: '400px',
      boxShadow: '0px 2px 10px rgba(0,0,0,0.2)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ padding: '10px', backgroundColor: '#f0f0f0', borderBottom: '1px solid #ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        Chatbot
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.2em', cursor: 'pointer' }}>X</button>
      </div>
      <div style={{ flexGrow: 1, padding: '10px', overflowY: 'auto' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <span style={{
              display: 'inline-block',
              padding: '8px 12px',
              borderRadius: '15px',
              backgroundColor: msg.sender === 'user' ? '#007bff' : '#e2e2e2',
              color: msg.sender === 'user' ? 'white' : 'black',
              maxWidth: '80%'
            }}>
              {msg.text}
              {msg.sources && msg.sources.length > 0 && (
                <div style={{ fontSize: '0.7em', marginTop: '5px', opacity: 0.7 }}>
                  Sources: {msg.sources.join(', ')}
                </div>
              )}
            </span>
          </div>
        ))}
        {isLoading && (
          <div style={{ textAlign: 'left', margin: '5px 0' }}>
            <span style={{
              display: 'inline-block',
              padding: '8px 12px',
              borderRadius: '15px',
              backgroundColor: '#e2e2e2',
              color: 'black',
              maxWidth: '80%'
            }}>
              Thinking...
            </span>
          </div>
        )}
        {errorMessage && ( // Display error message prominently
          <div style={{ color: 'red', textAlign: 'center', marginTop: '10px' }}>
            Error: {errorMessage}
          </div>
        )}
      </div>
      <div style={{ padding: '10px', borderTop: '1px solid #ccc', display: 'flex' }}>
        <input
          type="text"
          placeholder="Type your question..."
          style={{ flexGrow: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '5px', marginRight: '5px' }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
          disabled={isLoading}
        />
        <button onClick={handleSendMessage} style={{ padding: '8px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }} disabled={isLoading}>Send</button>
      </div>
    </div>
  );
};

export default ChatInterface;