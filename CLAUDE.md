# Wolfram Alpha MCP Server Project

## MCP (Model Context Protocol) Overview

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications to connect to external data sources and tools. It follows a client-server architecture where:

- **Hosts** are LLM applications (like Claude Desktop) that initiate connections
- **Clients** maintain 1:1 connections with servers inside the host
- **Servers** provide context, tools, and prompts to clients

## MCP Server Architecture

### Core Components
1. **Base Protocol**: JSON-RPC 2.0 message handling (mandatory)
2. **Lifecycle Management**: Initialization and capability negotiation (mandatory)
3. **Server Features**: Resources, prompts, and tools (optional)

### Key Capabilities
- **Tools**: Executable functions that allow LLMs to take actions
- **Resources**: Readable data sources (files, APIs, databases)
- **Prompts**: Reusable templates for LLM interactions

## TypeScript SDK Key Components

### Main Classes
- `McpServer` - High-level server interface (recommended)
- `Server` - Low-level server class for advanced control
- `ResourceTemplate` - For dynamic resource URIs with parameters

### Transport Options
- **stdio**: Process-based communication (best for command-line tools)
- **HTTP Streamable**: HTTP-based streaming (best for web services)
- **WebSocket**: Real-time bidirectional communication

## Streamable HTTP Transport Details

### Architecture
- Uses **HTTP POST** for client-to-server communication
- Uses **Server-Sent Events (SSE)** for server-to-client communication
- Built on **JSON-RPC 2.0** message format
- Supports both stateful (with sessions) and stateless modes

### Key Features
- **Session Management**: Uses `mcp-session-id` header for stateful connections
- **Security**: DNS rebinding protection, CORS support, authentication
- **Resumability**: SSE event IDs and `Last-Event-ID` header support
- **Error Handling**: Comprehensive HTTP status codes and JSON-RPC errors

### Implementation Patterns

#### Express.js Integration
```typescript
import express from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const app = express();
app.use(express.json());

// Stateful session management
const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};

app.post('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  let transport: StreamableHTTPServerTransport;

  if (sessionId && transports[sessionId]) {
    transport = transports[sessionId];
  } else if (!sessionId && isInitializeRequest(req.body)) {
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sessionId) => {
        transports[sessionId] = transport;
      },
      enableDnsRebindingProtection: true,
      allowedHosts: ['127.0.0.1'],
    });
    
    const server = new McpServer({ name: "wolfram-server", version: "1.0.0" });
    await server.connect(transport);
  }

  await transport.handleRequest(req, res, req.body);
});
```

### Installation Commands
```bash
# Use bun for package management
bun install @modelcontextprotocol/sdk zod

# Development
bun run dev

# Build
bun run build
```

### Security Considerations
- **DNS Rebinding Protection**: Enable for local servers
- **Origin Validation**: Validate `Origin` headers
- **HTTPS/TLS**: Required for production deployments
- **Authentication**: OAuth 2.1 support available
- **Rate Limiting**: Implement DoS protection

### Content Types and Headers
- **Requests**: `Accept: application/json, text/event-stream`
- **JSON Responses**: `Content-Type: application/json`
- **SSE Streams**: `Content-Type: text/event-stream`
- **Session Header**: `mcp-session-id` for stateful connections
- **Protocol Version**: `MCP-Protocol-Version: <version>`

## Current Implementation Status

### Project Structure
The project currently contains a **Cloudflare Worker-based MCP server** implementation:

```
wolfram-mcp-worker/
├── src/
│   └── index.ts              # Main worker entry point with calculator tools
├── package.json              # Dependencies and scripts
├── wrangler.jsonc           # Cloudflare Worker configuration
├── tsconfig.json            # TypeScript configuration
├── biome.json               # Code formatting and linting
└── worker-configuration.d.ts # Generated types for Cloudflare Workers
```

### Current Implementation
- **Platform**: Cloudflare Workers with Durable Objects
- **Framework**: Uses `agents/mcp` package (v0.0.100) with MCP SDK v1.13.1
- **Package Manager**: Yarn (configured in package.json)
- **Transport**: HTTP-based with SSE support via `/sse` and `/mcp` endpoints
- **Build Tool**: Wrangler v4.22.0 for Cloudflare deployment

### Implemented Tools
Currently implements **calculator functionality** (placeholder):
1. `add` - Simple addition of two numbers
2. `calculate` - Multi-operation calculator (add, subtract, multiply, divide)

### Dependencies
- `@modelcontextprotocol/sdk` v1.13.1 - MCP TypeScript SDK
- `agents` v0.0.100 - MCP agent framework
- `zod` v3.25.67 - Schema validation
- Development tools: TypeScript, Biome, Wrangler

### Deployment Configuration
- **Name**: `wolfram-mcp-worker`
- **Runtime**: Node.js compatibility enabled
- **Durable Objects**: `MyMCP` class for stateful operations
- **Endpoints**: 
  - `/sse` and `/sse/message` for Server-Sent Events
  - `/mcp` for MCP protocol communication

### Next Steps for Wolfram Alpha Integration
1. **Replace calculator tools** with Wolfram Alpha API integration
2. **Add environment variables** for `WOLFRAM_ALPHA_API_KEY` in wrangler.jsonc
3. **Implement Wolfram-specific tools**:
   - `wolfram-query`: Execute Wolfram Alpha queries
   - `wolfram-simple`: Simple text-based queries
   - `wolfram-full`: Full result queries with step-by-step solutions
4. **Add HTTP client** for Wolfram Alpha API calls
5. **Update server name** from "Authless Calculator" to "Wolfram Alpha MCP Server"

### Setup Instructions

1. **Get a Wolfram Alpha API Key:**
   - Visit https://products.wolframalpha.com/api/
   - Sign up for a free developer account
   - Create a new app to get your API key

2. **For Local Development:**
   ```bash
   # Create .dev.vars file in project root (already in .gitignore)
   echo "WOLFRAM_ALPHA_API_KEY=your-actual-api-key-here" > .dev.vars
   echo "AUTH_TOKEN=$(openssl rand -base64 32)" >> .dev.vars
   ```

3. **For Production Deployment:**
   ```bash
   # Set the API key as a secret (recommended for security)
   wrangler secret put WOLFRAM_ALPHA_API_KEY
   # Enter your Wolfram Alpha API key when prompted
   
   # Set the auth token as a secret
   wrangler secret put AUTH_TOKEN
   # Enter a secure random token when prompted (generate with: openssl rand -base64 32)
   ```

### Development Commands
```bash
# Local development with .dev.vars
yarn dev  # or wrangler dev

# Deploy to Cloudflare
yarn deploy  # or wrangler deploy

# Type checking
yarn type-check

# Linting and formatting
yarn lint:fix
yarn format

# Manage production secrets
wrangler secret put WOLFRAM_ALPHA_API_KEY    # Set Wolfram API key
wrangler secret put AUTH_TOKEN               # Set auth token
wrangler secret list                         # List all secrets
wrangler secret delete WOLFRAM_ALPHA_API_KEY # Delete API key
wrangler secret delete AUTH_TOKEN            # Delete auth token
```

### Local Development Secret Access Methods

**Method 1: .dev.vars File (Recommended)**
```bash
# Create .dev.vars file in project root
echo "WOLFRAM_ALPHA_API_KEY=your-api-key" > .dev.vars
echo "AUTH_TOKEN=$(openssl rand -base64 32)" >> .dev.vars
yarn dev
```

**Method 2: Environment Variables**
```bash
# Set environment variables directly
WOLFRAM_ALPHA_API_KEY=your-api-key AUTH_TOKEN=your-auth-token yarn dev
```

**Method 3: Temporary vars in wrangler.jsonc**
```jsonc
{
  "vars": {
    "WOLFRAM_ALPHA_API_KEY": "your-api-key-for-testing",
    "AUTH_TOKEN": "your-auth-token-for-testing"
  }
}
```

**Note:** `.dev.vars` is already in `.gitignore` and is the safest method for local development.

## Authentication

The MCP endpoints (`/mcp` and `/sse`) require Bearer token authentication:

```bash
# Test endpoints with authentication
curl -H "Authorization: Bearer your-auth-token" http://localhost:8787/mcp
curl -H "Authorization: Bearer your-auth-token" http://localhost:8787/sse

# Health endpoint (no auth required)
curl http://localhost:8787/health
```

**Security Features:**
- ✅ Bearer token authentication on all MCP endpoints
- ✅ Configurable auth token via Wrangler secrets
- ✅ Auth bypass for health/status endpoints
- ✅ Proper HTTP status codes (401 Unauthorized, 403 Forbidden)
- ✅ Development mode warning when auth is disabled