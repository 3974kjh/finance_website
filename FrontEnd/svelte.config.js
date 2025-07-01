import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// Static adapter for CloudFlare Pages (정적 사이트)
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',  // SPA fallback
			precompress: false,
			strict: true
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
