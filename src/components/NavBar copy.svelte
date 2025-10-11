<script context="module">
  import { navigate } from 'svelte-routing';
  
  export function goTo(path) {
    navigate(path);
  }
</script>

<script>
  import { onMount, onDestroy } from 'svelte';

  let isOpen = false;
  let pathname = '/';
  
  function toggleNavbar() {
    isOpen = !isOpen;
  }

  // Función local que actualiza pathname y cierra navbar
  function navigateAndClose(path) {
    goTo(path);
    isOpen = false;
    pathname = path; // Actualizar manualmente
  }

  function isActive(path) {
    return pathname === path;
  }

  // Actualizar pathname cuando cambia la ruta
  onMount(() => {
    pathname = window.location.pathname;
    
    // Escuchar cambios de navegación
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(this, args);
      pathname = window.location.pathname;
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(this, args);
      pathname = window.location.pathname;
    };
    
    // Escuchar evento popstate (navegación con botones atrás/adelante)
    const handlePopState = () => {
      pathname = window.location.pathname;
    };
    
    window.addEventListener('popstate', handlePopState);
    
    return () => {
      history.pushState = originalPushState;
      history.replaceState = originalReplaceState;
      window.removeEventListener('popstate', handlePopState);
    };
  });
</script>

<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" role="button" on:click={() => navigateAndClose('/')}>
      <i class="fa fa-code" aria-hidden="true"></i> MDE LLM SQL Generator
    </a>

    <button
      class="navbar-toggler"
      type="button"
      on:click={toggleNavbar}
      aria-controls="navbarNav"
      aria-expanded={isOpen}
      aria-label="Toggle navigation"
    >
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class={`collapse navbar-collapse ${isOpen ? 'show' : ''}`} id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a
            class="nav-link {isActive('/') ? 'active' : ''}"
            role="button"
            on:click={() => navigateAndClose('/')}
            aria-current="{isActive('/') ? 'page' : undefined}"
          >
            Inicio
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link {isActive('/projects') ? 'active' : ''}"
            role="button"
            on:click={() => navigateAndClose('/projects')}
            aria-current="{isActive('/projects') ? 'page' : undefined}"
          >
            Proyectos
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link {isActive('/about') ? 'active' : ''}"
            role="button"
            on:click={() => navigateAndClose('/about')}
            aria-current="{isActive('/about') ? 'page' : undefined}"
          >
            Acerca de
          </a>
        </li>
      </ul>
    </div>
  </div>
</nav>