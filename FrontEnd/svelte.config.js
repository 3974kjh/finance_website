import adapter from '@sveltejs/adapter-cloudflare';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// CloudFlare Pages adapter for deployment
		adapter: adapter({
			// CloudFlare Pages에서 Edge Runtime을 사용하지 않는 경우
			routes: {
				include: ['/*'],
				exclude: ['<all>']
			}
		}),
		csrf: {
			checkOrigin: false
		}
	}
};

export default config;
