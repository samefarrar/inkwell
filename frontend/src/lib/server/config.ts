import { env } from '$env/dynamic/private';

export const INTERNAL_API_URL = env.INTERNAL_API_URL ?? 'http://localhost:8000';
