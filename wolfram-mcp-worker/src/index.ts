import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { withAuth } from "./auth.js";
import { WolframLanguageClient } from "./wolfram_backend.js";

// Define our MCP agent with tools
export class MyMCP extends McpAgent {
  private wolframLanguageClient?: WolframLanguageClient;

  // @ts-ignore - Ignore type conflict between SDK versions
  server = new McpServer({
    name: "Wolfram MCP Server",
    version: "1.0.0",
  });

  async init() {
    // Initialize Wolfram Language Server client
    const wolframServerUrl =
      (this.env as any)?.WOLFRAM_LANGUAGE_SERVER_URL || "http://localhost:8000";
    this.wolframLanguageClient = new WolframLanguageClient(wolframServerUrl);

    // Wolfram Alpha natural language query tool
    this.server.tool(
      "wolfram_alpha",
      {
        query: z.string().describe("Natural language query for Wolfram Alpha"),
        timeout: z
          .number()
          .optional()
          .default(30)
          .describe("Query timeout in seconds (1-300)"),
        format: z
          .string()
          .optional()
          .default("Result")
          .describe("Wolfram Alpha result format"),
      },
      async ({
        query,
        timeout,
        format,
      }: {
        query: string;
        timeout?: number;
        format?: string;
      }) => {
        if (!this.wolframLanguageClient) {
          return {
            content: [
              {
                type: "text",
                text: "Error: Wolfram Language Server client not initialized.",
              },
            ],
          };
        }

        try {
          // First check if the server is available
          const connection = await this.wolframLanguageClient.testConnection();
          if (!connection.available) {
            return {
              content: [
                {
                  type: "text",
                  text: `Error: Wolfram Language Server not available: ${connection.error}`,
                },
              ],
            };
          }

          // Query Wolfram Alpha
          const response = await this.wolframLanguageClient.queryWolframAlpha({
            query,
            timeout: timeout || 30,
            format: format || "Result",
          });

          if (!response.success) {
            return {
              content: [
                {
                  type: "text",
                  text: `Wolfram Alpha query failed: ${response.error || "Unknown error"}`,
                },
              ],
            };
          }

          // Format the response
          let resultText = "";
          if (response.output) {
            resultText = response.output;
          } else if (response.result) {
            resultText =
              typeof response.result === "string"
                ? response.result
                : JSON.stringify(response.result, null, 2);
          } else {
            resultText = "Query completed successfully (no output)";
          }

          if (response.execution_time) {
            resultText += `\n\n*Query time: ${response.execution_time.toFixed(3)}s*`;
          }

          return {
            content: [
              {
                type: "text",
                text: resultText,
              },
            ],
          };
        } catch (error) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          return {
            content: [
              {
                type: "text",
                text: `Error querying Wolfram Alpha: ${errorMessage}`,
              },
            ],
          };
        }
      },
    );

    // Wolfram Language execution tool (strict syntax)
    this.server.tool(
      "wolfram_execute",
      {
        code: z
          .string()
          .describe("Wolfram Language code to execute (strict syntax)"),
        timeout: z
          .number()
          .optional()
          .default(30)
          .describe("Execution timeout in seconds (1-300)"),
      },
      async ({ code, timeout }: { code: string; timeout?: number }) => {
        if (!this.wolframLanguageClient) {
          return {
            content: [
              {
                type: "text",
                text: "Error: Wolfram Language Server client not initialized.",
              },
            ],
          };
        }

        try {
          // First check if the server is available
          const connection = await this.wolframLanguageClient.testConnection();
          if (!connection.available) {
            return {
              content: [
                {
                  type: "text",
                  text: `Error: Wolfram Language Server not available: ${connection.error}`,
                },
              ],
            };
          }

          // Execute the Wolfram code
          const response = await this.wolframLanguageClient.executeWolfram({
            code,
            timeout: timeout || 30,
          });

          if (!response.success) {
            return {
              content: [
                {
                  type: "text",
                  text: `Wolfram execution failed: ${response.error || "Unknown error"}`,
                },
              ],
            };
          }

          // Format the response
          let resultText = "";
          if (response.output) {
            resultText = response.output;
          } else if (response.result) {
            resultText =
              typeof response.result === "string"
                ? response.result
                : JSON.stringify(response.result, null, 2);
          } else {
            resultText = "Execution completed successfully (no output)";
          }

          if (response.execution_time) {
            resultText += `\n\n*Execution time: ${response.execution_time.toFixed(3)}s*`;
          }

          return {
            content: [
              {
                type: "text",
                text: resultText,
              },
            ],
          };
        } catch (error) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          return {
            content: [
              {
                type: "text",
                text: `Error executing Wolfram code: ${errorMessage}`,
              },
            ],
          };
        }
      },
    );
  }
}

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);

    // Create authenticated handlers
    const authToken = (env as any)?.AUTH_TOKEN;
    const authenticatedHandler = withAuth(authToken);

    if (url.pathname === "/sse" || url.pathname === "/sse/message") {
      return authenticatedHandler((req: Request, env: any, ctx: any) =>
        MyMCP.serveSSE("/sse").fetch(req, env, ctx),
      )(request, env, ctx);
    }

    if (url.pathname === "/mcp") {
      return authenticatedHandler((req: Request, env: any, ctx: any) =>
        MyMCP.serve("/mcp").fetch(req, env, ctx),
      )(request, env, ctx);
    }

    // Health check endpoint (unauthenticated)
    if (url.pathname === "/health" || url.pathname === "/") {
      return new Response(
        JSON.stringify({
          status: "ok",
          service: "Wolfram MCP Server",
          version: "1.0.0",
          endpoints: {
            mcp: "/mcp",
            sse: "/sse",
          },
          auth: authToken ? "required" : "disabled",
        }),
        {
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    return new Response("Not found", { status: 404 });
  },
};
