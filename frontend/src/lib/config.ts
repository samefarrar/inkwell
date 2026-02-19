/** Centralized API configuration — uses env vars with dev defaults. */

/**
 * REST API base URL — client-side fetches go through the SvelteKit API proxy
 * so the httpOnly auth cookie is forwarded to the backend.
 * Server-side code (load functions) uses INTERNAL_API_URL from env.
 */
export const BASE_API_URL =
	typeof window !== 'undefined' ? '' : 'http://localhost:8322';

export const BASE_WS_URL =
	(typeof window !== 'undefined'
		? (import.meta.env.VITE_PUBLIC_WS_URL as string)
		: undefined) || 'ws://localhost:8322/ws';
