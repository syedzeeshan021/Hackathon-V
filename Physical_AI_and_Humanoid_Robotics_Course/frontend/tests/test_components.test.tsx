import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInterface from '../src/components/Chatbot/ChatInterface'; // Assuming relative path

// Mock the API service and UserContext if needed for isolated testing
jest.mock('../src/services/api', () => ({
  chatWithBot: jest.fn(() => Promise.resolve({ answer: 'Mocked bot response', sources: [] })),
}));

// Mock useUser hook if ChatInterface depends on it
jest.mock('../src/contexts/UserContext', () => ({
  useUser: () => ({
    user: { id: 'test', email: 'test@example.com', background: 'NONE', token: 'mock-token' },
    isLoading: false,
    error: null,
    updateUserBackground: jest.fn(),
  }),
}));


describe('ChatInterface', () => {
  it('renders without crashing', () => {
    render(<ChatInterface onClose={() => {}} />);
    expect(screen.getByText(/Chatbot/i)).toBeInTheDocument();
  });

  it('displays initial bot message', () => {
    render(<ChatInterface onClose={() => {}} />);
    expect(screen.getByText(/Hello! How can I help you/i)).toBeInTheDocument();
  });

  // More comprehensive tests would involve simulating user input and interaction
  // For this placeholder, we focus on basic rendering.
});
