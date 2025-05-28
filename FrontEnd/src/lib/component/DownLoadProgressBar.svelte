<script lang="ts">
  export let min: number = 0;
  export let max: number = 100;
  export let nowCount: number;

  $: percentage = Math.round(((nowCount - min) / (max - min)) * 100);
  $: progressWidth = `${percentage}%`;
</script>

<div class="download-progress">
  <div class="progress-bar">
    <div class="progress" style="width: {progressWidth}"></div>
  </div>
  <div class="percentage">{percentage}%</div>
</div>

<style>
  .download-progress {
    width: 100%;
    max-width: 300px;
    margin: 20px auto;
  }

  .progress-bar {
    width: 100%;
    height: 20px;
    background-color: #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
  }

  .progress {
    height: 100%;
    background-color: #808080;
    transition: width 0.3s ease;
  }

  .percentage {
    text-align: center;
    margin-top: 10px;
    font-weight: bold;
  }
</style>
