import React from 'react';
import ChatWidget from './chatUI/BrowserOnlyChatWidget';

export default function Root({ children }) {
  return (
    <>
      {children}
      <ChatWidget />
    </>
  );
}