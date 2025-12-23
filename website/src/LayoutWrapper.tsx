import React from 'react';
import { Layout } from '@docusaurus/core';
import ChatWidget from './components/chatUI/ChatWidget';

export default function LayoutWrapper(props) {
  return (
    <Layout {...props}>
      {props.children}
      <ChatWidget />
    </Layout>
  );
}