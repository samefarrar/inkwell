import { fail, redirect } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { INTERNAL_API_URL } from '$lib/server/config';
import type { Actions } from './$types';

export const actions = {
	default: async ({ request, cookies }) => {
		const form = await request.formData();
		const name = form.get('name');
		const email = form.get('email');
		const password = form.get('password');

		if (typeof name !== 'string' || typeof email !== 'string' || typeof password !== 'string') {
			return fail(400, { name: name?.toString() ?? '', email: email?.toString() ?? '', error: 'All fields are required' });
		}

		if (password.length < 8) {
			return fail(400, { name, email, error: 'Password must be at least 8 characters' });
		}

		const res = await fetch(`${INTERNAL_API_URL}/api/auth/register`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name, email, password })
		});

		if (!res.ok) {
			const data = await res.json().catch(() => null);
			const message = data?.detail ?? 'Registration failed';
			return fail(res.status, { name, email, error: message });
		}

		const { token } = await res.json();
		cookies.set('access_token', token, {
			path: '/',
			httpOnly: true,
			sameSite: 'lax',
			secure: env.ENV !== 'development',
			maxAge: 86400
		});

		redirect(303, '/dashboard');
	}
} satisfies Actions;
