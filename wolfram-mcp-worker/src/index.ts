import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { WolframAlphaClient } from "./wolfram.js";
import { withAuth } from "./auth.js";

// Define our MCP agent with tools
export class MyMCP extends McpAgent {
	private wolframClient?: WolframAlphaClient;

	// @ts-ignore - Ignore type conflict between SDK versions
	server = new McpServer({
		name: "Wolfram Alpha MCP Server",
		version: "1.0.0",
	});

	async init() {
		// Initialize Wolfram Alpha client if API key secret is available
		const apiKey = (this.env as any)?.WOLFRAM_ALPHA_API_KEY;
		if (apiKey) {
			this.wolframClient = new WolframAlphaClient(apiKey);
		}

		// Wolfram Alpha query tool
		this.server.tool(
			"wolfram_query",
			{
				query: z.string().describe("The query to send to Wolfram Alpha"),
				format: z
					.enum(["simple", "full"])
					.default("simple")
					.describe(
						"Response format: 'simple' for text-only, 'full' for detailed results with images",
					),
			},
			async ({
				query,
				format,
			}: {
				query: string;
				format: "simple" | "full";
			}) => {
				if (!this.wolframClient) {
					return {
						content: [
							{
								type: "text",
								text: "Error: Wolfram Alpha API key not configured. Please set WOLFRAM_ALPHA_API_KEY secret using 'wrangler secret put WOLFRAM_ALPHA_API_KEY'.",
							},
						],
					};
				}

				try {
					if (format === "simple") {
						const result = await this.wolframClient.simpleQuery(query);
						return {
							content: [{ type: "text", text: result }],
						};
					} else {
						const result = await this.wolframClient.fullQuery(query);
						let response = `**Query:** ${result.input}\n**Timing:** ${result.timing}s\n\n`;

						for (const pod of result.pods) {
							response += `**${pod.title}:**\n`;
							if (pod.content) {
								response += `${pod.content}\n`;
							}
							if (pod.images && pod.images.length > 0) {
								response += `Images: ${pod.images.map((img) => `![${img.alt}](${img.src})`).join(", ")}\n`;
							}
							response += "\n";
						}

						if (result.assumptions && result.assumptions.length > 0) {
							response += "**Assumptions:**\n";
							for (const assumption of result.assumptions) {
								response += `- ${assumption.word} (${assumption.type}): ${assumption.values.map((v) => v.desc).join(", ")}\n`;
							}
							response += "\n";
						}

						if (result.warnings && result.warnings.length > 0) {
							response += "**Warnings:**\n";
							for (const warning of result.warnings) {
								response += `- ${warning}\n`;
							}
						}

						return {
							content: [{ type: "text", text: response }],
						};
					}
				} catch (error) {
					const errorMessage =
						error instanceof Error ? error.message : "Unknown error occurred";
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

		// Simple math calculator (fallback when Wolfram Alpha is not available)
		this.server.tool(
			"calculate",
			{
				operation: z.enum(["add", "subtract", "multiply", "divide"]),
				a: z.number(),
				b: z.number(),
			},
			async ({
				operation,
				a,
				b,
			}: {
				operation: "add" | "subtract" | "multiply" | "divide";
				a: number;
				b: number;
			}) => {
				let result: number;
				switch (operation) {
					case "add":
						result = a + b;
						break;
					case "subtract":
						result = a - b;
						break;
					case "multiply":
						result = a * b;
						break;
					case "divide":
						if (b === 0)
							return {
								content: [
									{
										type: "text",
										text: "Error: Cannot divide by zero",
									},
								],
							};
						result = a / b;
						break;
				}
				return { content: [{ type: "text", text: String(result) }] };
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
			return authenticatedHandler(
				(req: Request, env: any, ctx: any) => MyMCP.serveSSE("/sse").fetch(req, env, ctx)
			)(request, env, ctx);
		}

		if (url.pathname === "/mcp") {
			return authenticatedHandler(
				(req: Request, env: any, ctx: any) => MyMCP.serve("/mcp").fetch(req, env, ctx)
			)(request, env, ctx);
		}

		// Health check endpoint (unauthenticated)
		if (url.pathname === "/health" || url.pathname === "/") {
			return new Response(JSON.stringify({
				status: "ok",
				service: "Wolfram Alpha MCP Server",
				version: "1.0.0",
				endpoints: {
					mcp: "/mcp",
					sse: "/sse"
				},
				auth: authToken ? "required" : "disabled"
			}), {
				headers: { "Content-Type": "application/json" }
			});
		}

		return new Response("Not found", { status: 404 });
	},
};
