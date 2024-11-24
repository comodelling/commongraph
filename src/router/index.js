import { createRouter, createWebHistory } from 'vue-router';
import Layout from '../components/Layout.vue';
import MainPage from '../views/MainPage.vue';
import Focus from '../views/Focus.vue';
import About from '../views/About.vue';

const routes = [
  {
    path: '/',
    name: 'MainPage',
    component: Layout, // Use Layout here
    children: [ // Define child routes for nested view under Layout
      {
        path: '',
        component: MainPage,
      },
      {
        path: '/about',
        name: 'About',
        component: About,
      },
      {
        path: '/view/:id',
        name: 'Focus',
        component: Focus,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;