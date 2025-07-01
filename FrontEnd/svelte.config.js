import adapter from '@sveltejs/adapter-cloudflare';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// CloudFlare Pages adapter with Functions support
		adapter: adapter({
			routes: {
				include: ['/api/*'],  // API 라우트만 서버 함수로 처리
				exclude: ['<build>', '<prerendered>']  // 빌드된 정적 파일들은 제외
			}
		}),
		csrf: {
			checkOrigin: false
		}
	}
};

export default config;
