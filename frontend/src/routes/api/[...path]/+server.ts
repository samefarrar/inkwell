/**
 * API proxy — forwards client-side API requests to the backend with the auth cookie.
 *
 * Client-side JS can't send the httpOnly cookie cross-origin, so all API calls
 * go through this proxy which reads the cookie from the SvelteKit request and
 * forwards it to the backend.
 */

import { INTERNAL_API_URL } from '$lib/server/config';
import type { RequestHandler } from './$types';

async function proxy(event: Parameters<RequestHandler>[0]): Promise<Response> {
	const token = event.cookies.get('access_token');
	const headers: Record<string, string> = {};

	if (token) {
		headers['Cookie'] = `access_token=${token}`;
	}

	// Forward content-type for requests with bodies
	const contentType = event.request.headers.get('content-type');
	if (contentType) {
		headers['Content-Type'] = contentType;
	}

	const url = `${INTERNAL_API_URL}/api/${event.params.path}${event.url.search}`;
	const body = ['GET', 'HEAD'].includes(event.request.method)
		? undefined
		: await event.request.arrayBuffer();

	const res = await fetch(url, {
		method: event.request.method,
		headers,
		body
	});

	return new Response(res.body, {
		status: res.status,
		headers: {
			'Content-Type': res.headers.get('Content-Type') ?? 'application/json'
		}
	});
}

export const GET: RequestHandler = proxy;
export const POST: RequestHandler = proxy;
export const PUT: RequestHandler = proxy;
export const DELETE: RequestHandler = proxy;
export const PATCH: RequestHandler = proxy;
