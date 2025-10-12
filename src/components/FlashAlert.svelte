<script>
  import { onMount, createEventDispatcher } from 'svelte';
  
  export let message = '';
  export let type = 'success'; // 'success' | 'danger' | 'warning' | 'info'
  export let duration = 4000; // Duración en milisegundos
  export let dismissible = true;
  export let position = 'fixed'; // 'fixed' | 'absolute' | 'relative'
  
  const dispatch = createEventDispatcher();
  let show = false;
  let timeoutId = null;

  onMount(() => {
    // Mostrar el alert cuando se monta
    show = true;
    
    // Auto-ocultar si tiene duración
    if (duration > 0) {
      timeoutId = setTimeout(() => {
        close();
      }, duration);
    }
  });

  function close() {
    show = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    
    // Emitir evento después de la animación
    setTimeout(() => {
      dispatch('close');
    }, 300);
  }

  // Limpiar timeout al desmontar
  $: if (!show && timeoutId) {
    clearTimeout(timeoutId);
    timeoutId = null;
  }
</script>

{#if show}
  <div 
    class="alert {type === 'success' ? 'alert-success' : type === 'danger' ? 'alert-danger' : type === 'warning' ? 'alert-warning' : 'alert-info'} {dismissible ? 'alert-dismissible' : ''} fade show shadow-sm" 
    role="alert"
    class:position-{position}="{position !== 'relative'}"
    class:top-0="{position !== 'relative'}"
    class:start-50="{position !== 'relative'}"
    class:translate-middle-x="{position !== 'relative'}"
    class:mt-2="{position !== 'relative'}"
    class:w-100="{position !== 'relative'}"
  >
    <div class="d-flex align-items-center">
      {#if type === 'success'}
        <i class="fa fa-check-circle me-2"></i>
      {:else if type === 'danger'}
        <i class="fa fa-exclamation-triangle me-2"></i>
      {:else if type === 'warning'}
        <i class="fa fa-exclamation-circle me-2"></i>
      {:else}
        <i class="fa fa-info-circle me-2"></i>
      {/if}
      
      <span class="flex-grow-1">{message}</span>
      
      {#if dismissible}
        <button 
          type="button" 
          class="btn-close ms-2" 
          on:click={close} 
          aria-label="Cerrar"
        ></button>
      {/if}
    </div>
  </div>
{/if}

<style>
  /* Animaciones adicionales si las necesitas */
  .alert {
    transition: all 0.3s ease;
    z-index: 9999;
  }
</style>