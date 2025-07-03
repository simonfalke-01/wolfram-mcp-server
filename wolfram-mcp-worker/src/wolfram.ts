interface WolframAlphaResponse {
	queryresult: {
		success: boolean;
		error?: boolean;
		numpods: number;
		datatypes?: string;
		timedout?: string;
		timedoutpods?: string;
		timing: number;
		parsetiming: number;
		parsetimedout: boolean;
		recalculate: string;
		id: string;
		host: string;
		server: string;
		related: string;
		version: string;
		inputstring?: string;
		pods?: Array<{
			title: string;
			scanner: string;
			id: string;
			position: number;
			error?: boolean;
			numsubpods: number;
			subpods: Array<{
				title: string;
				plaintext?: string;
				img?: {
					src: string;
					alt: string;
					title: string;
					width: number;
					height: number;
				};
			}>;
		}>;
		assumptions?: Array<{
			type: string;
			word: string;
			template: string;
			count: number;
			values: Array<{
				name: string;
				desc: string;
				input: string;
			}>;
		}>;
		warnings?: {
			count: number;
			text: string[];
		};
	};
}

export class WolframAlphaClient {
	private apiKey: string;
	private baseUrl = "https://api.wolframalpha.com/v2/query";

	constructor(apiKey: string) {
		this.apiKey = apiKey;
	}

	async query(
		input: string,
		options: {
			format?: string[];
			output?: string;
			includepodid?: string;
			excludepodid?: string;
			podtitle?: string;
			podindex?: string;
			scanner?: string;
			async?: boolean;
			ip?: string;
			latlong?: string;
			location?: string;
			assumption?: string;
			podstate?: string;
			units?: string;
			width?: number;
			maxwidth?: number;
			plotwidth?: number;
			mag?: number;
			scantimeout?: number;
			podtimeout?: number;
			formattimeout?: number;
			parsetimeout?: number;
			totaltimeout?: number;
			reinterpret?: boolean;
			translation?: boolean;
			ignorecase?: boolean;
			sig?: string;
		} = {},
	): Promise<WolframAlphaResponse> {
		const params = new URLSearchParams({
			appid: this.apiKey,
			input: input,
			output: options.output || "json",
			format: options.format?.join(",") || "plaintext",
			...Object.fromEntries(
				Object.entries(options)
					.filter(
						([key, value]) =>
							key !== "format" && key !== "output" && value !== undefined,
					)
					.map(([key, value]) => [key, String(value)]),
			),
		});

		const url = `${this.baseUrl}?${params.toString()}`;

		const response = await fetch(url, {
			method: "GET",
			headers: {
				"User-Agent": "Wolfram MCP Server/1.0.0",
			},
		});

		if (!response.ok) {
			throw new Error(
				`Wolfram Alpha API request failed: ${response.status} ${response.statusText}`,
			);
		}

		const data = (await response.json()) as WolframAlphaResponse;

		if (!data.queryresult.success) {
			throw new Error(
				`Wolfram Alpha query failed: ${data.queryresult.error ? "API error" : "Unknown error"}`,
			);
		}

		return data;
	}

	async simpleQuery(input: string): Promise<string> {
		try {
			const response = await this.query(input, {
				format: ["plaintext"],
				output: "json",
			});

			if (
				!response.queryresult.pods ||
				response.queryresult.pods.length === 0
			) {
				return "No results found for your query.";
			}

			// Extract plaintext from pods
			const results: string[] = [];

			for (const pod of response.queryresult.pods) {
				if (pod.subpods && pod.subpods.length > 0) {
					for (const subpod of pod.subpods) {
						if (subpod.plaintext?.trim()) {
							results.push(`**${pod.title}:**\n${subpod.plaintext}`);
						}
					}
				}
			}

			return results.length > 0
				? results.join("\n\n")
				: "No text results available.";
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Wolfram Alpha query failed: ${error.message}`);
			}
			throw new Error("Wolfram Alpha query failed: Unknown error");
		}
	}

	async fullQuery(input: string): Promise<{
		success: boolean;
		input: string;
		timing: number;
		pods: Array<{
			title: string;
			content: string;
			images?: Array<{
				src: string;
				alt: string;
				width: number;
				height: number;
			}>;
		}>;
		assumptions?: Array<{
			type: string;
			word: string;
			values: Array<{
				name: string;
				desc: string;
			}>;
		}>;
		warnings?: string[];
	}> {
		try {
			const response = await this.query(input, {
				format: ["plaintext", "image"],
				output: "json",
			});

			const result = {
				success: response.queryresult.success,
				input: response.queryresult.inputstring || input,
				timing: response.queryresult.timing,
				pods: [] as Array<{
					title: string;
					content: string;
					images?: Array<{
						src: string;
						alt: string;
						width: number;
						height: number;
					}>;
				}>,
				assumptions: response.queryresult.assumptions?.map((assumption) => ({
					type: assumption.type,
					word: assumption.word,
					values: assumption.values.map((value) => ({
						name: value.name,
						desc: value.desc,
					})),
				})),
				warnings: response.queryresult.warnings?.text,
			};

			if (response.queryresult.pods) {
				for (const pod of response.queryresult.pods) {
					const podData = {
						title: pod.title,
						content: "",
						images: [] as Array<{
							src: string;
							alt: string;
							width: number;
							height: number;
						}>,
					};

					if (pod.subpods) {
						const textParts: string[] = [];
						for (const subpod of pod.subpods) {
							if (subpod.plaintext?.trim()) {
								textParts.push(subpod.plaintext.trim());
							}
							if (subpod.img) {
								podData.images.push({
									src: subpod.img.src,
									alt: subpod.img.alt,
									width: subpod.img.width,
									height: subpod.img.height,
								});
							}
						}
						podData.content = textParts.join("\n");
					}

					if (podData.content || podData.images.length > 0) {
						result.pods.push(podData);
					}
				}
			}

			return result;
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Wolfram Alpha query failed: ${error.message}`);
			}
			throw new Error("Wolfram Alpha query failed: Unknown error");
		}
	}
}
