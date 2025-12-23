import React from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';

const ChatWidget = () => {
  return (
    <BrowserOnly
      fallback={
        <div className="chat-widget-placeholder" style={{ display: 'none' }}>
          Loading chat widget...
        </div>
      }
    >
      {() => {
        const ChatWidgetDynamic = require('./ChatWidget').default;
        return <ChatWidgetDynamic />;
      }}
    </BrowserOnly>
  );
};

export default ChatWidget;