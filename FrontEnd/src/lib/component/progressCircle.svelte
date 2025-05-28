<script lang="ts">
  export let size: number = 50; // 로딩 서클의 크기 (기본값: 50px)
  export let color: string = "#3498db"; // 로딩 서클의 색상 (기본값: 파란색)
  export let thickness: number = 5; // 서클 두께 (기본값: 4px)
  export let text: string = "Loading..."; // 로딩 서클 아래에 표시할 텍스트
  export let isLarge: boolean = false;
  export let isTextBlack: boolean = true;
</script>

<div class="loading-container">
  <div
    class="loading-circle"
    style="
      width: {size}px;
      height: {size}px;
      border-width: {thickness}px;
      border-color: {color} transparent transparent transparent;
    "
  ></div>
  {#if text}
    <div class="{isLarge ? 'loading-lg-text' : 'loading-text'}" style="color: {isTextBlack ? '#000000' : '#FFFFFF'}">{text}</div>
  {/if}
</div>

<style>
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .loading-circle {
    display: inline-block;
    border-style: solid;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    margin-top: 10px;
    font-size: 14px;
    font-weight: bold;
    /* color: #555; */
    text-align: center;
  }

  .loading-lg-text {
    margin-top: 10px;
    font-size: 18px;
    font-weight: bold;
    /* color: #FFFFFF; */
    text-align: center;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
