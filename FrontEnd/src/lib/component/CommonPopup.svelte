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
	<div class="absolute left-0 top-0 w-full h-full bg-gray-200 opacity-50" style="z-index: 10" />
{/if}

<!-- 메인 팝업  -->
<div class="fixed {className}" bind:this={mainContainer} style="z-index: {zIndex}; {modalPositionType === 'center' ? 'opacity: 0; transition: opacity 0.1s ease-in-out;' : ''}" >
	<div class="flex justify-center items-center h-full">
		<div class="flex flex-col shadow-lg bg-white popup-wrap">
			<!-- 팝업 타이틀 창 -->
			<div id="commonDialog" class="text-white p-2 bg-gray-600 flex justify-between {isMoving} 'cursor-move' :'cursor-arrow'" role="none" on:mousedown={mouseDownOnTitle}>
				<span class="font-bold">{titleName}</span>
				{#if !isHideCloseBtn}
					<button class="w-[1.4rem] h-[1.4rem]" on:click={closeEvent} {disabled}>
						<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g id="Group 197">
								<path id="Line" d="M11.2088 1.30936L1.30928 11.2089" stroke="#8696CC" stroke-width="1.5" stroke-linecap="round" />
								<path id="Line_2" d="M11.2088 11.2089L1.30929 1.30936" stroke="#8696CC" stroke-width="1.5" stroke-linecap="round" />
							</g>
						</svg>
					</button>
				{/if}
			</div>
			<!-- 메인 표시 항목 -->
			<slot />
			<!-- 하단 표시 항목 -->
			<footer class="p-2 bg-gray-600">
				<slot name="subInfo" />
			</footer>
		</div>
	</div>
</div>

<!--
@component
## Props
#### Input Parameters : titleName, isModal
@prop	export let titleName: string = '타이틀명';
@prop	export let isModal: boolean = true;
-->
