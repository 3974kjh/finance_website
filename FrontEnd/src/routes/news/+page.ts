import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	return {
		title: '실시간 뉴스'
	};
}; 