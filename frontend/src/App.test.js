import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders LEVIATHAN app', () => {
  render(<App />);
  const titleElement = screen.getByText(/LEVIATHAN/i);
  expect(titleElement).toBeInTheDocument();
});