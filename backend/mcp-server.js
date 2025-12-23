#!/usr/bin/env node

import { serve } from '@upstash/context7-mcp';

// Configure the MCP server with stdio transport
const config = {
  transport: 'stdio',
};

console.log('Starting MCP server with stdio transport...');
serve(config);