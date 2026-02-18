import { error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { PageServerLoad } from './$types';

const INTERNAL_API_URL = env.INTERNAL_API_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ params, cookies }) => {
	const token = cookies.get('access_token');
	const res = await fetch(`${INTERNAL_API_URL}/api/sessions/${params.id}`, {
		headers: token ? { Cookie: `access_token=${token}` } : {}
	});

	if (!res.ok) {
		error(404, 'Session not found');
	}

	const sessionData = await res.json();
	if (!sessionData.found) {
		error(404, 'Session not found');
	}

	return { sessionData };
};
