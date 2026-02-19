import { redirect, type Handle } from '@sveltejs/kit';
import { jwtVerify } from 'jose';
import { env } from '$env/dynamic/private';
import type { User } from '$lib/types/user';

const getSecret = () => new TextEncoder().encode(env.JWT_SECRET_KEY ?? '');

export const handle: Handle = async ({ event, resolve }) => {
	const token = event.cookies.get('access_token');

	if (token) {
		try {
			const { payload } = await jwtVerify(token, getSecret());
			const sub = payload.sub;
			const email = payload.email;
			const name = payload.name;
			const plan = payload.plan;
			if (
				typeof sub !== 'string' ||
				typeof email !== 'string' ||
				typeof name !== 'string' ||
				typeof plan !== 'string'
			) {
				throw new Error('Invalid JWT claims');
			}
			event.locals.user = {
				id: Number(sub),
				email,
				name,
				plan: plan as User['plan']
			};
		} catch {
			event.locals.user = null;
			event.cookies.delete('access_token', { path: '/' });
		}
	} else {
		event.locals.user = null;
	}

	// Route group based matching
	const routeId = event.route.id ?? '';
	const isAppRoute = routeId.startsWith('/(app)');

	if (isAppRoute && !event.locals.user) {
		const returnTo = encodeURIComponent(event.url.pathname);
		redirect(303, `/login?returnTo=${returnTo}`);
	}

	const isAuthRoute =
		routeId.startsWith('/(marketing)/login') || routeId.startsWith('/(marketing)/register');
	if (isAuthRoute && event.locals.user) {
		redirect(303, '/dashboard');
	}

	return resolve(event);
};
