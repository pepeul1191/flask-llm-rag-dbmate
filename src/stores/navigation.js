import { writable } from 'svelte/store';
import { navigate } from 'svelte-routing';

// Store para el pathname actual
export const currentPath = writable('/');

// Función de navegación que actualiza el store
export function goTo(path) {
  navigate(path);
  currentPath.set(path);
}

// Inicializar con la ruta actual
if (typeof window !== 'undefined') {
  currentPath.set(window.location.pathname);
}