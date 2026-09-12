import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],cacheDir:'.cache/vite',server:{host:'127.0.0.1',port:5275,strictPort:true,proxy:{'/api':{target:'http://127.0.0.1:8766',changeOrigin:false}}},preview:{host:'127.0.0.1',port:5275},build:{outDir:'dist'}});
