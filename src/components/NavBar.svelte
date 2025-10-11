<script>
  import { navigate, useLocation } from 'svelte-routing';
  import { onMount } from 'svelte';

  let isOpen = false;
  
  // CORRECTO: usar useLocation para reactividad
  
  // Variable reactiva para el pathname
  $: pathname = window.location.pathname;

  function toggleNavbar() {
    isOpen = !isOpen;
  }

  function goTo(path) {
    navigate(path);

    isOpen = false;
    pathname = path;
    console.log(pathname)
  }

  // onMount para inicialización si es necesaria
  onMount(() => {
    console.log('Navbar montado, ruta actual:', pathname);
    // Cualquier inicialización adicional aquí
  });

  // Función helper para verificar ruta activa
   function isActive(path) {
    return pathname === path;
  }
</script>

<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" role="button" on:click={() => goTo('/')}><i class="fa fa-code" aria-hidden="true"></i>MDE LLM SQL Generator</a>

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
            class="nav-link {pathname =='/' ? 'active' : ''}"
            role="button"
            on:click={() => goTo('/')}
            aria-current="{pathname =='/' ? 'page' : undefined}"
          >
            Inicio
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link {pathname =='/projects' ? 'active' : ''}"
            role="button"
            on:click={() => goTo('/projects')}
            aria-current="{pathname =='/projects' ? 'page' : undefined}"
          >
            Proyectos
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link {pathname =='/about' ? 'active' : ''}"
            role="button"
            on:click={() => goTo('/about')}
            aria-current="{pathname =='/about' ? 'page' : undefined}"
          >
            Acerca de
          </a>
        </li>
      </ul>
    </div>
  </div>
</nav>

<style>
  .nav-link.active {
    font-weight: 500;
  }
</style>