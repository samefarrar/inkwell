import { error } from '@sveltejs/kit';
import { INTERNAL_API_URL } from '$lib/server/config';
import type { PageServerLoad } from './$types';

interface SessionDetail {
	found: boolean;
	session_id: number;
	task_type: string;
	topic: string;
	status: string;
	created_at: string;
	interview_messages: Array<{
		role: string;
		content: string;
		thought_json?: string | null;
		search_json?: string | null;
		ready_json?: string | null;
		ordering: number;
	}>;
	rounds: Record<
		string,
		Array<{
			title: string;
			angle: string;
			content: string;
			word_count: number;
			draft_index: number;
		}>
	>;
	highlights: Array<{
		draft_index: number;
		start: number;
		end: number;
		text: string;
		sentiment: 'like' | 'flag';
		label?: string;
		note?: string;
	}>;
}

export const load: PageServerLoad = async ({ params, cookies }) => {
	const token = cookies.get('access_token');
	const res = await fetch(`${INTERNAL_API_URL}/api/sessions/${params.id}`, {
		headers: token ? { Cookie: `access_token=${token}` } : {}
	});

	if (!res.ok) {
		error(404, 'Session not found');
	}

	const sessionData: SessionDetail = await res.json();
	if (!sessionData.found) {
		error(404, 'Session not found');
	}

	return { sessionData };
};
