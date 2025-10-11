<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentPath, goTo } from '../stores/navigation.js';

  let isOpen = false;
  let pathname = '';
  
  // Suscribirse al store
  const unsubscribe = currentPath.subscribe(value => {
    pathname = value;
  });

  function toggleNavbar() {
    isOpen = !isOpen;
  }

  // Función local que cierra el navbar al navegar
  function navigateAndClose(path) {
    goTo(path);
    isOpen = false;
  }

  function isActive(path) {
    return pathname === path;
  }

  onMount(() => {
    console.log('Navbar montado, ruta actual:', pathname);
  });

  onDestroy(() => {
    // Limpiar suscripción
    unsubscribe();
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

<style>
  .nav-link {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 0.375rem;
    margin: 0 0.125rem;
  }
  
  .nav-link:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  .nav-link.active {
    font-weight: 600;
    color: #0d6efd !important;
    background-color: rgba(13, 110, 253, 0.15);
  }
  
  .navbar-brand {
    cursor: pointer;
    font-weight: 600;
  }
</style>