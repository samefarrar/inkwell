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
	const headers: Record<string, string> = token ? { Cookie: `access_token=${token}` } : {};

	const [sessionsRes, prefsRes] = await Promise.all([
		fetch(`${INTERNAL_API_URL}/api/sessions`, { headers }),
		fetch(`${INTERNAL_API_URL}/api/preferences`, { headers })
	]);

	const sessions: SessionSummary[] = sessionsRes.ok ? await sessionsRes.json() : [];
	const prefs = prefsRes.ok ? await prefsRes.json() : {};

	return {
		sessions,
		onboarding_completed: prefs.onboarding_completed ?? false,
		last_style_id: prefs.last_style_id ?? null
	};
};
