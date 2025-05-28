<script lang="ts">
	import { MultiChartBasic, SingleChartBasic } from '$lib/main';

	let innerHeight: number = 0;
	let innerWidth: number = 0;

	let isSingleMode: boolean = false;

	let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
		detailInfo: any
	} | null = null;

</script>

<svelte:window bind:innerHeight bind:innerWidth/>
<div class="w-full h-full relative">
	<MultiChartBasic
		fullChartViewerWidth={innerWidth - 100}
		fullChartViewerHeight={innerHeight}
		on:showDetailChartViewerCallback={(e) => {
			singleChartInfo = e.detail;
			isSingleMode = true;
		}}
	/>
	{#if isSingleMode}
		<SingleChartBasic
			{singleChartInfo}
			on:closeSingleChartModeCallback={() => {
				isSingleMode = false;
				singleChartInfo = null;
			}}
		/>
	{/if}
</div>

<style>
  :global(body) {
    overflow: hidden;
  }
  :global(html) {
    overflow: hidden;
  }
</style>