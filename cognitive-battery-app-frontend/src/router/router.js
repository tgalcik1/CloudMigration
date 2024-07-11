import { createRouter, createWebHistory } from 'vue-router';
import Signin from '@/views/signin/signin.vue';
import Home from '@/views/home/home.vue';
import Presurvey from '@/views/presurvey/presurvey.vue';
import Setup from '@/views/setup/setup.vue';
import Baseline from '@/views/baseline/baseline.vue';
import Video from '@/views/baseline/video.vue';
import Instructions from '@/views/game/instructions.vue';
import GameView from '@/views/game/game.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true, hidden: true }
  },
  {
    path: '/signin',
    name: 'signin',
    component: Signin,
    meta: { hidden: true }
  },
  {
    path: '/presurvey',
    name: 'presurvey',
    component: Presurvey,
    meta: { requiresAuth: true }
  },
  {
    path: '/setup',
    name: 'setup',
    component: Setup,
    meta: { requiresAuth: true }
  },
  {
    path: '/baseline',
    name: 'baseline',
    component: Baseline,
    meta: { requiresAuth: true }
  },
  {
    path: '/video',
    name: 'video',
    component: Video,
    meta: { requiresAuth: true, hidden: true }
  },
  {
    path: '/instructions',
    name: 'instructions',
    component: Instructions,
    meta: { requiresAuth: true, hidden: true }
  },
  {
    path: '/game',
    name: 'game',
    component: GameView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const loggedIn = !!localStorage.getItem('user');
  if (to.matched.some(record => record.meta.requiresAuth) && !loggedIn) {
    next('/signin');
  } else {
    next();
  }
});

export default router;
