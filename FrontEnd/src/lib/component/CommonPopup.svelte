<script lang="ts">
	import { onMount, createEventDispatcher, onDestroy } from 'svelte';
	import _ from 'lodash';

	export let titleName: string = '타이틀명'; // string
	export let isModal: boolean = true;
	export let disabled: boolean = false;
	export let modalPositionType: string | 'center' | 'custom' = 'center';
	export let left: number = 0;
	export let top: number = 0;
	export let isHideCloseBtn: boolean = false;
	export let className = '';
	/**
	 * ESC키 누를 때 팝업 닫기 여부
	 * @description 기본값은 닫음(true)
	 */
	export let isClosedWhenEscapeKeyPressed: boolean = true;

	const dispatch = createEventDispatcher();

	let mainContainer: HTMLElement;
	let isMoving: boolean = false;
	let width: number, height: number;

	let zIndex: number = 20;

	/**
	 * 닫기 버튼 클릭 시, dialog 종료 이벤트 실행
	 */
	const closeEvent = () => {
		dispatch('closedDialogCallback');
	};

	/**
	 * props 데이터 타입 유효성 검사
	 */
	const checkPropsValidation = () => {
		if (typeof titleName !== 'string') {
			throw new Error('props 인자 type 불일치');
		}
	};

	/**
	 * 'esc'키 입력 시, dialog 종료 이벤트 실행
	 *
	 * @param event
	 */
	const keyupInInwodw = (event: KeyboardEvent) => {
		if (isClosedWhenEscapeKeyPressed === false) {
			return;
		}

		// 마지막으로 뜬 팝업 컴포넌트를 닫는다.
		if (event.key == 'Escape') {
			closeEvent();
		}
	};

	/**
	 * mount되기 전에 props validation 체크
	 */
	checkPropsValidation();

	onMount(() => {
		if (modalPositionType === 'center') {
			// DOM 렌더링 완료 후 중앙 정렬
			setTimeout(() => {
				moveToCenterInScreen();
			}, 10);
		} else {
			moveToCustomInScreen(top, left);
		}
	});

	/**
	 * 마우스 다운 이벤트를 처리한다.
	 * @param event
	 */
	const mouseDownOnTitle = (event: MouseEvent) => {
		if (isModal === true) {
			return;
		}

		isMoving = true;

		const rect = mainContainer.getBoundingClientRect();

		left = rect.left;
		top = rect.top;
	};

	/**
	 * 마우스 이동 이벤트를 처리한다.
	 * @param event
	 */
	const mouseMoveInWindow = (event: MouseEvent) => {
		if (isModal === true) {
			return;
		}

		event.preventDefault();

		if (isMoving === false) {
			return;
		}

		left += event.movementX;
		top += event.movementY;

		calcPositionForPopup();
	};

	/**
	 * 마우스 업 이벤트를 처리한다.
	 * @param event
	 */
	const mouseUpInWindow = (event: MouseEvent) => {
		isMoving = false;
	};

	/**
	 * 팝업의 위치를 재계산하여 배치한다.
	 */
	const calcPositionForPopup = () => {
		if (isModal === true) {
			return;
		}

		mainContainer.style.top = `${top}px`;
		mainContainer.style.left = `${left}px`;
	};

	/**
	 * 사용자가 준 top, left 위치에 화면을 배치한다.
	 */
	export const moveToCustomInScreen = (top: number, left: number) => {
		mainContainer.style.top = `${top}px`;
		mainContainer.style.left = `${left}px`;
	};

	/**
	 * 화면 중앙으로 이동
	 */
	const moveToCenterInScreen = (): void => {
		if (!mainContainer) return;

		// DOM이 완전히 렌더링될 때까지 잠시 대기
		setTimeout(() => {
			const containerRect = mainContainer.getBoundingClientRect();
			const viewportHeight = window.innerHeight;
			const viewportWidth = window.innerWidth;

			// 중앙 위치 계산 (간단한 방식)
			const centerX = (viewportWidth - containerRect.width) / 2;
			const centerY = (viewportHeight - containerRect.height) / 2;

			// 최소 여백 보장 (20px)
			const finalX = Math.max(20, centerX);
			const finalY = Math.max(20, centerY);

			// 위치 설정
			mainContainer.style.left = `${finalX}px`;
			mainContainer.style.top = `${finalY}px`;
			
			// 중앙 정렬 완료 후 팝업을 보이게 설정
			if (modalPositionType === 'center') {
				mainContainer.style.opacity = '1';
			}
		}, 0);
	};
</script>

<svelte:window on:mousemove={mouseMoveInWindow} on:mouseup={mouseUpInWindow} on:resize={() => {
	if (modalPositionType === 'center' && mainContainer) {
		moveToCenterInScreen();
	} else {
		calcPositionForPopup();
	}
}} on:keyup={keyupInInwodw} />

<!-- 팝업 배경 -->
{#if isModal}
	<div class="fixed inset-0 w-screen h-screen bg-black/40 backdrop-blur-md" style="z-index: 50" />
{/if}

<!-- 메인 팝업  -->
<div class="fixed {className}" bind:this={mainContainer} style="z-index: 60; {modalPositionType === 'center' ? 'opacity: 0; transition: opacity 0.3s ease-in-out;' : ''}" >
	<div class="flex justify-center items-center h-full p-4">
		<div class="flex flex-col shadow-2xl bg-white/95 backdrop-blur-lg popup-wrap rounded-2xl overflow-hidden hover:shadow-3xl transition-all duration-300 max-h-[95vh] w-full">
			<!-- 팝업 타이틀 창 -->
			<div id="commonDialog" class="text-white p-4 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 flex justify-between items-center border-b border-white/10 transition-all duration-200 flex-shrink-0 {isMoving ? 'cursor-move' : 'cursor-default'}" role="none" on:mousedown={mouseDownOnTitle}>
				<span class="font-bold text-lg flex items-center">
					<svg class="w-5 h-5 mr-2 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
					</svg>
					{titleName}
				</span>
				{#if !isHideCloseBtn}
					<button class="w-8 h-8 rounded-full bg-white/10 hover:bg-red-500/80 backdrop-blur-sm border border-white/20 hover:border-red-300/50 flex items-center justify-center transition-all duration-200 hover:scale-110 shadow-md hover:shadow-lg group" on:click={closeEvent} {disabled}>
						<svg class="w-4 h-4 text-white group-hover:text-white transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
						</svg>
					</button>
				{/if}
			</div>
			<!-- 메인 표시 항목 -->
			<div class="bg-white/90 backdrop-blur-md flex-grow min-h-0 overflow-hidden">
				<slot />
			</div>
			<!-- 하단 표시 항목 -->
			<footer class="p-2 bg-gradient-to-r from-slate-600 to-slate-700 border-t border-white/10 flex-shrink-0">
				<div class="text-white">
					<slot name="subInfo" />
				</div>
			</footer>
		</div>
	</div>
</div>

<style>
	.popup-wrap {
		min-width: 300px;
		max-width: 95vw;
		min-height: 200px;
	}
	
	/* 향상된 그림자 효과 - 떠있는 느낌 */
	.shadow-3xl {
		box-shadow: 
			0 60px 120px -20px rgba(0, 0, 0, 0.3),
			0 35px 60px -12px rgba(0, 0, 0, 0.25),
			0 15px 25px -5px rgba(0, 0, 0, 0.1),
			0 0 0 1px rgba(255, 255, 255, 0.05);
	}
	
	/* 기본 그림자도 강화 */
	.shadow-2xl {
		box-shadow: 
			0 25px 50px -12px rgba(0, 0, 0, 0.25),
			0 10px 20px -5px rgba(0, 0, 0, 0.1),
			0 0 0 1px rgba(255, 255, 255, 0.05);
	}
</style>

<!--
@component
## Props
#### Input Parameters : titleName, isModal
@prop	export let titleName: string = '타이틀명';
@prop	export let isModal: boolean = true;
-->
