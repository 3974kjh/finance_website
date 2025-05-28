<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { page } from "$app/stores";
	import { Toaster } from 'svelte-french-toast';

	// toast 간격 설정
	const toastGutter: number = 10;

	// toast 간격 설정
	const toastReverseOrder: boolean = true;

	const toastPosition:
		| 'top-center'
		| 'top-left'
		| 'top-right'
		| 'top-start'
		| 'top-end'
		| 'bottom-center'
		| 'bottom-left'
		| 'bottom-right'
		| 'bottom-start'
		| 'bottom-end'
		| undefined = 'top-center';

	/**
	 * toast option
	 */
	const toastOptions = {
		id: 'toast',
		position: undefined,
		style: 'padding: 8px 12px; color: #000; background-color: #fff; border-radius: 2px;',
		className: 'toast-info',
		error: {
			className: 'toast-error'
		},
		success: {
			className: 'toast-success'
		}
	};
</script>

<Toaster gutter={toastGutter} reverseOrder={toastReverseOrder} position={toastPosition} {toastOptions} />
<div class="flex flex-row w-screen h-screen bg-gray-600">
	<div class="flex flex-col w-[100px] h-full border-r-2 p-2 space-y-2 bg-gray-600">
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/`)}>HOME</button>
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/analyze' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/analyze`)}>ANALYZE</button>
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/statistic' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/statistic`)}>STATISTIC</button>
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/webSearch' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/webSearch`)}>SEARCH</button>
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/invest' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/invest`)}>INVEST</button>
		<button class="flex px-1 w-full items-start {$page.url.pathname === '/timeLine' ? 'bg-gray-300 font-bold border-l-2 border-white' : 'text-white'}" on:click={() => goto(`${base}/timeLine`)}>TIMELINE</button>
	</div>
	<div class="flex w-[calc(100%_-_100px)] h-full">
		<slot />
	</div>
</div>