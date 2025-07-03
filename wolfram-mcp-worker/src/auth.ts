/**
 * Authentication utilities for Bearer token validation
 */

export class AuthError extends Error {
	constructor(message: string, public status: number = 401) {
		super(message);
		this.name = 'AuthError';
	}
}

export interface AuthResult {
	success: boolean;
	error?: string;
}

export class Auth {
	private authToken: string;

	constructor(authToken: string) {
		this.authToken = authToken;
	}

	/**
	 * Validates the Authorization header against the stored auth token
	 */
	validateRequest(request: Request): AuthResult {
		const authHeader = request.headers.get('Authorization');
		
		if (!authHeader) {
			return {
				success: false,
				error: 'Missing Authorization header'
			};
		}

		if (!authHeader.startsWith('Bearer ')) {
			return {
				success: false,
				error: 'Invalid Authorization header format. Expected: Bearer <token>'
			};
		}

		const token = authHeader.substring(7); // Remove 'Bearer ' prefix
		
		if (!token) {
			return {
				success: false,
				error: 'Missing bearer token'
			};
		}

		if (token !== this.authToken) {
			return {
				success: false,
				error: 'Invalid bearer token'
			};
		}

		return { success: true };
	}

	/**
	 * Creates an unauthorized response
	 */
	static createUnauthorizedResponse(error: string): Response {
		return new Response(
			JSON.stringify({
				error: 'Unauthorized',
				message: error
			}),
			{
				status: 401,
				headers: {
					'Content-Type': 'application/json',
					'WWW-Authenticate': 'Bearer'
				}
			}
		);
	}

	/**
	 * Creates a forbidden response
	 */
	static createForbiddenResponse(error: string): Response {
		return new Response(
			JSON.stringify({
				error: 'Forbidden',
				message: error
			}),
			{
				status: 403,
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
	}
}

/**
 * Auth middleware that validates bearer token before allowing request to proceed
 */
export function withAuth(authToken: string | undefined) {
	return function(handler: (request: Request, env: any, ctx: any) => Promise<Response>) {
		return async function(request: Request, env: any, ctx: any): Promise<Response> {
			// If no auth token is configured, skip auth (for development)
			if (!authToken) {
				console.warn('Warning: AUTH_TOKEN not configured. Skipping authentication.');
				return handler(request, env, ctx);
			}

			const auth = new Auth(authToken);
			const authResult = auth.validateRequest(request);
			
			if (!authResult.success) {
				return Auth.createUnauthorizedResponse(authResult.error || 'Authentication failed');
			}

			return handler(request, env, ctx);
		};
	};
}