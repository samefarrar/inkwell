export interface User {
	id: number;
	email: string;
	name: string;
	plan: 'free' | 'pro' | 'team';
}

export type UserPlan = User['plan'];
