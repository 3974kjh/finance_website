import adapter from '@sveltejs/adapter-cloudflare';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// CloudFlare Pages adapter with optimized Functions support
		adapter: adapter({
			routes: {
				include: ['/api/*'],  // API 라우트만 서버 함수로 처리
				exclude: ['<build>', '<prerendered>']  // 빌드된 정적 파일들은 제외
			},
			platformProxy: {
				configPath: 'wrangler.toml',
				experimentalJsonConfig: true
			}
		}),
		csrf: {
			checkOrigin: false
		},
		// CloudFlare Pages 배포 최적화
		serviceWorker: {
			register: false  // CloudFlare Pages에서는 Service Worker 비활성화
		},
		version: {
			pollInterval: 0  // 폴링 비활성화로 성능 향상
		}
	}
};

export default config;
