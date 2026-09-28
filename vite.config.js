import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Relative asset paths: the built site works at any address —
  // https://<user>.github.io/pnt-graft-atlas/, a university server, or a custom domain.
  base: './',
});
