import type { PageLoad } from './$types';

// CloudFlare Pages에서 SSR 문제 해결을 위해 client-side 렌더링만 사용
export const ssr = false;
export const prerender = false;

export const load: PageLoad = async () => {
	return {
		title: '실시간 뉴스'
	};
}; 