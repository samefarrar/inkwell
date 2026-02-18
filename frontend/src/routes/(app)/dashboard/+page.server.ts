import { env } from '$env/dynamic/private';
import type { PageServerLoad } from './$types';

const INTERNAL_API_URL = env.INTERNAL_API_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ cookies }) => {
	const token = cookies.get('access_token');
	const res = await fetch(`${INTERNAL_API_URL}/api/sessions`, {
		headers: token ? { Cookie: `access_token=${token}` } : {}
	});

	if (!res.ok) {
		return { sessions: [] };
	}

	const sessions = await res.json();
	return { sessions };
};
