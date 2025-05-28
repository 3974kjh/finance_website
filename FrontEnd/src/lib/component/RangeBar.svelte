<script lang="ts">
  export let value: number = 50;
  export let min: number = 200;
  export let max: number = 3000;

  function handleInput(event: Event) {
    value = Number((event.target as HTMLInputElement).value);
  }
</script>

<div class="rangebar-container">
  <input 
    type="range" 
    autocomplete="off"
    min={min}
    max={max}
    bind:value 
    on:input={handleInput}
  />
  <span>{value}</span>
</div>

<style>
  .rangebar-container {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  input[type="range"] {
    width: 200px;
  }
</style>