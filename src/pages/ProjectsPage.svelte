<script>
  import { onMount } from 'svelte';
  import ProjectCard from '../components/ProjectCard.svelte';
  import ModalProjectForm from '../forms/ModalProjectForm.svelte';
  import { fetchProjects, deleteProject as deleteProjectService } from '../services/projects_service.js';
  import FlashAlert from '../components/FlashAlert.svelte';

  let projects = []

  onMount(() => {
    listProjects();
  })

  let selectedProject = null;
  let showAlert = false;
  let alertMessage = '';
  let alertType = 'success';
  let modalRef;

  function listProjects(){
    fetchProjects().then((resp) => {
      projects = resp.data;
    }).catch((resp) => {
      console.log(resp);
    });
  }

  function handleAlertClose() {
    showAlert = false;
    alertMessage = '';
  }

  function createProject() {
    selectedProject = null;
    modalRef.clear();
    modalRef.show();
  }

  function editProject(project) {
    console.log(project)
    selectedProject = project;
    modalRef.show();
  }

  function showFlashAlert(message, type = 'success') {
    alertMessage = message;
    alertType = type;
    showAlert = true;
  }

  function deleteProject(project) {
    if (confirm(`¿Eliminar el proyecto "${project.title}"?`)) {
      deleteProjectService(project.id).then((resp) => {
        listProjects();
        showFlashAlert(resp.message, 'success' );
      });
    }
  }
</script>

<svelte:head>
  <title>Lista de Proyectos</title>
</svelte:head>

<div class="projects-simple w-100">
  <div class="d-flex justify-content-between align-items-center mb-4 px-3">
    <h2 class="h4 fw-bold text-dark mb-0">Proyectos recientes</h2>
    <button class="btn btn-primary d-flex align-items-center" on:click={createProject}>
      <i class="fa fa-plus"></i> Crear proyecto
    </button>
  </div>

  <hr class="my-4 mx-3" />

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

  <div class="projects-flex-container w-100 d-flex flex-wrap gap-3 px-3">
    <div class="project-flex-card flex-fill" style="min-width: 300px; max-width: 400px;" on:click={createProject}>
      <div class="card h-100 border-2 border-dashed bg-light">
        <div class="card-body d-flex flex-column align-items-center justify-content-center text-center text-muted">
          <i class="fa fa-plus fa-2x mb-2"></i>
          <span class="fw-bold">Crear proyecto</span>
        </div>
      </div>
    </div>

    {#each projects as project (project.id)}
      <ProjectCard {project} 
      on:edit={e => editProject(e.detail)}
      on:delete={e => deleteProject(e.detail)} />
    {/each}
  </div>
</div>

<ModalProjectForm
  bind:this={modalRef}
  {selectedProject}
  project={selectedProject}
  on:refreshList={listProjects}
/>

<style>
  .projects-simple {
    width: 100%;
    margin-bottom: 50px;
    padding-top: 10px;
  }

  .projects-flex-container {
    gap: 1.5rem;
  }

  .project-flex-card .card {
    transition: all 0.3s ease;
    border-radius: 8px;
    min-height: 150px;
  }

  .project-flex-card .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1) !important;
  }

  .border-dashed {
    border-style: dashed !important;
    border-color: #adb5bd !important;
    cursor: pointer;
  }

  .border-dashed:hover {
    border-color: #0d6efd !important;
    background: #f8f9fa !important;
  }

  .card-title {
    font-size: 1rem;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .projects-flex-container {
      gap: 1rem;
    }
    
    .project-flex-card {
      min-width: 100% !important;
      max-width: 100% !important;
    }
  }

   .project-flex-card .card {
    transition: all 0.3s ease;
    border-radius: 12px;
  }

  .project-flex-card .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
  }

  .project-icon {
    transition: all 0.3s ease;
  }

  .project-flex-card .card:hover .project-icon {
    transform: scale(1.1);
    background-color: rgba(13, 110, 253, 0.15) !important;
  }

  .card-title {
    font-size: 1rem;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .dropdown-menu {
    border: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
  }

  .dropdown-item {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .dropdown-item:hover {
    
  }
</style>