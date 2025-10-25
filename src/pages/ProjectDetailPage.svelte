<!-- src/pages/ProjectDetailPage.svelte -->
<script>
  import { createImage, fetchProject } from '../services/projects_service.js';
  import { onMount } from 'svelte';
  import ModalProjectForm from '../forms/ModalProjectForm.svelte';
  import UploadPUMLForm from '../forms/UploadPUMLForm.svelte';
  import FlashAlert from '../components/FlashAlert.svelte';

  export let id;
  let showAlert = false;
  let alertMessage = '';
  let alertType = 'success';
  let modalRef;
  let modalUMLRef;

  onMount(() => {
    fetchProject(id).then((resp) => {
      project = resp.data;
    }).catch((resp) => {
      console.log(resp);
    });
  });

  // Datos de ejemplo para el proyecto
  let project = {
    id: id,
    title: "Mi Proyecto",
    description: ``,
    imageUrl: "",
  };

  // Manejar cambios en la descripción
  function handleDescriptionChange(event) {
    project.description = event.target.value;
  }

  function editProject() {
    modalRef.show();
  }

  function addMigrations(){
    modalUMLRef.show();
  }

  function handleAlertClose() {
    showAlert = false;
    alertMessage = '';
  }
</script>

<svelte:head>
  <title>Editar Proyecto</title>
</svelte:head>

<ModalProjectForm
  bind:this={modalRef}
  showContinue={false} 
  {project}
/>

<UploadPUMLForm
  bind:this={modalUMLRef}
  {project}
/>

<div class="project w-100">
  {#if showAlert}
    <div class="px-3">
      <FlashAlert 
        message="{alertMessage}"
        type="{alertType}"
        duration={5000}
        position="absolute"
        on:close={handleAlertClose}
      />
    </div>
  {/if}

  <div class="d-flex justify-content-between align-items-center mb-4 px-3">
    <h2 class="h4 fw-bold text-dark mb-0">
      Modelo en PlantUML: {project.title}
    </h2>
    <div>
      <button class="btn btn-primary" on:click={editProject}>
        <i class="fa fa-pencil"></i>Editar Proyecto
      </button>
      <button class="btn btn-success" on:click={addMigrations}>
        <i class="fa fa-plus"></i>Agregar Migraciones
      </button>
    </div>
  </div>

  <div class="container-fluid">
    
  </div>
</div>

<style>
  .project {
    width: 100%;
    margin-bottom: 50px;
    padding-top: 10px;
  }

  textarea:focus {
    outline: none;
    box-shadow: none;
  }

  .card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border: 1px solid rgba(0, 0, 0, 0.125);
  }
</style>
