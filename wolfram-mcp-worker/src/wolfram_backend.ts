/**
 * HTTP client for calling the Wolfram Language Server backend API
 */

export interface WolframExecuteRequest {
	code: string;
	timeout?: number;
	format?: "text" | "json" | "image";
	kernel_path?: string;
}

export interface WolframEvaluateRequest {
	expression: string;
	timeout?: number;
}

export interface WolframResponse {
	success: boolean;
	result?: any;
	output?: string;
	error?: string;
	execution_time?: number;
	warnings?: string[];
}

export interface WolframEvaluateResponse {
	success: boolean;
	result?: any;
	error?: string;
	execution_time?: number;
}

export interface WolframHealthResponse {
	status: string;
	version: string;
	wolfram_available: boolean;
	kernel_info?: any;
}

export class WolframLanguageClient {
	private baseUrl: string;
	private timeout: number;

	constructor(baseUrl: string = "http://localhost:8000", timeout: number = 60000) {
		this.baseUrl = baseUrl.replace(/\/$/, ""); // Remove trailing slash
		this.timeout = timeout;
	}

	/**
	 * Check health status of the Wolfram Language Server
	 */
	async health(): Promise<WolframHealthResponse> {
		const response = await this.makeRequest("GET", "/health");
		return response as WolframHealthResponse;
	}

	/**
	 * Execute Wolfram Language code
	 */
	async execute(request: WolframExecuteRequest): Promise<WolframResponse> {
		const response = await this.makeRequest("POST", "/execute", request);
		return response as WolframResponse;
	}

	/**
	 * Evaluate a simple Wolfram Language expression
	 */
	async evaluate(request: WolframEvaluateRequest): Promise<WolframEvaluateResponse> {
		const response = await this.makeRequest("POST", "/evaluate", request);
		return response as WolframEvaluateResponse;
	}

	/**
	 * Make HTTP request to the Wolfram Language Server
	 */
	private async makeRequest(
		method: "GET" | "POST",
		endpoint: string,
		body?: any
	): Promise<any> {
		const url = `${this.baseUrl}${endpoint}`;
		
		const options: RequestInit = {
			method,
			headers: {
				"Content-Type": "application/json",
				"User-Agent": "Wolfram MCP Server/1.0.0",
			},
			signal: AbortSignal.timeout(this.timeout),
		};

		if (body && method === "POST") {
			options.body = JSON.stringify(body);
		}

		try {
			const response = await fetch(url, options);

			if (!response.ok) {
				let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
				
				try {
					const errorBody = await response.text();
					if (errorBody) {
						const parsed = JSON.parse(errorBody);
						if (parsed.detail) {
							errorMessage = parsed.detail;
						} else if (parsed.message) {
							errorMessage = parsed.message;
						}
					}
				} catch {
					// Ignore JSON parsing errors, use default message
				}

				throw new Error(`Wolfram Language Server error: ${errorMessage}`);
			}

			const responseText = await response.text();
			
			if (!responseText) {
				throw new Error("Empty response from Wolfram Language Server");
			}

			try {
				return JSON.parse(responseText);
			} catch (parseError) {
				throw new Error(`Invalid JSON response from Wolfram Language Server: ${responseText}`);
			}
		} catch (error) {
			if (error instanceof Error) {
				if (error.name === "AbortError" || error.name === "TimeoutError") {
					throw new Error(`Wolfram Language Server request timed out after ${this.timeout}ms`);
				}
				throw error;
			}
			throw new Error(`Unknown error communicating with Wolfram Language Server: ${String(error)}`);
		}
	}

	/**
	 * Test connection to the Wolfram Language Server
	 */
	async testConnection(): Promise<{ available: boolean; error?: string; version?: string }> {
		try {
			const health = await this.health();
			return {
				available: true,
				version: health.version,
			};
		} catch (error) {
			return {
				available: false,
				error: error instanceof Error ? error.message : String(error),
			};
		}
	}
}