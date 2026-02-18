import { fail, redirect } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { INTERNAL_API_URL } from '$lib/server/config';
import type { Actions } from './$types';

export const actions = {
	default: async ({ request, cookies, url }) => {
		const form = await request.formData();
		const email = form.get('email');
		const password = form.get('password');

		if (typeof email !== 'string' || typeof password !== 'string') {
			return fail(400, { email: email?.toString() ?? '', error: 'All fields required' });
		}

		const res = await fetch(`${INTERNAL_API_URL}/api/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});

		if (!res.ok) {
			return fail(401, { email, error: 'Invalid credentials' });
		}

		const { token } = await res.json();
		cookies.set('access_token', token, {
			path: '/',
			httpOnly: true,
			sameSite: 'lax',
			secure: env.ENV !== 'development',
			maxAge: 86400
		});

		// Validate returnTo — prevent open redirect
		const returnTo = url.searchParams.get('returnTo');
		const target =
			returnTo && returnTo.startsWith('/') && !returnTo.startsWith('//') && !returnTo.includes('\\')
				? returnTo
				: '/dashboard';

		redirect(303, target);
	}
} satisfies Actions;
