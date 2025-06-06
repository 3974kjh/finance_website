import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import commonjs from 'vite-plugin-commonjs';

export default defineConfig({
	plugins: [commonjs(),sveltekit()],
	server: {
		allowedHosts: true
	}
});
