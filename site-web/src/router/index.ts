import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/system/login/index.vue') },
    { path: '/', component: () => import('@/views/home/index.vue') },
    { path: '/forgot-password', component: () => import('@/views/system/password/index.vue') },
    // 新增 EEG 测试页面，需要登录
    { path: '/eeg', component: () => import('@/views/eeg/EEGHome.vue'), meta: { requiresAuth: true } },
  ],
})

const guestRoutes = ['/login', '/register', '/forgot-password']

router.beforeEach((to, _from) => {
  const token = getAccessToken()
  const requiresAuth = to.meta.requiresAuth !== false

  // 已登录用户不能访问 guest 路由
  if (token && guestRoutes.includes(to.path)) {
    return '/'
  }

  // 未登录用户访问需要登录的路由时跳转登录
  if (!token && requiresAuth && !guestRoutes.includes(to.path)) {
    return '/login'
  }

  return true
})

export default router