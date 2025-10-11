<script>
  import { Router, Route } from 'svelte-routing';
  import Navbar from '../components/NavBar.svelte';

  import HomePage from '../pages/HomePage.svelte';
	import ProjectsPage from '../pages/ProjectsPage.svelte';
  import AboutPage from '../pages/AboutPage.svelte';
</script>

<Navbar />

<main>
	<Router>
		<Route path="/" component={HomePage} />
		<Route path="/projects" component={ProjectsPage} />
		<Route path="/about" component={AboutPage} />
	</Router>
</main>

<footer class="simple-footer">
  <p>Desarrollado por <strong>José Valdivia Caballero</strong></p>
</footer>

<style>
  .simple-footer {
    border-top: 1px solid #dee2e6;
    padding: 1rem;
    margin-top: auto;
    text-align: right;
    color: #6c757d;
		padding-bottom: 0px;
  }

	main{
		margin-top: 60px;
	}
</style>