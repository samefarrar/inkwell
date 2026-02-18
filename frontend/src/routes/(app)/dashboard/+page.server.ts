import { INTERNAL_API_URL } from '$lib/server/config';
import type { PageServerLoad } from './$types';

interface SessionSummary {
	id: number;
	task_type: string;
	topic: string;
	status: string;
	draft_count: number;
	created_at: string;
}

export const load: PageServerLoad = async ({ cookies }) => {
	const token = cookies.get('access_token');
	const res = await fetch(`${INTERNAL_API_URL}/api/sessions`, {
		headers: token ? { Cookie: `access_token=${token}` } : {}
	});

	if (!res.ok) {
		return { sessions: [] };
	}

	const sessions: SessionSummary[] = await res.json();
	return { sessions };
};
