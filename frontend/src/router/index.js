import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true, title: '工作台' }
  },
  {
    path: '/tickets',
    name: 'Tickets',
    component: () => import('@/views/Tickets.vue'),
    meta: { requiresAuth: true, title: '工单列表' }
  },
  {
    path: '/tickets/:id',
    name: 'TicketDetail',
    component: () => import('@/views/TicketDetail.vue'),
    meta: { requiresAuth: true, title: '工单详情' }
  },
  {
    path: '/create',
    name: 'CreateTicket',
    component: () => import('@/views/CreateTicket.vue'),
    meta: { requiresAuth: true, title: '创建工单' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: { requiresAuth: true, title: '协商聊天' }
  },
  {
    path: '/sla-monitor',
    name: 'SlaMonitor',
    component: () => import('@/views/SlaMonitor.vue'),
    meta: { requiresAuth: true, title: 'SLA监控', roles: ['admin', 'arbitrator'] }
  },
  {
    path: '/rules',
    name: 'Rules',
    component: () => import('@/views/Rules.vue'),
    meta: { requiresAuth: true, title: '规则引擎', roles: ['admin'] }
  },
  {
    path: '/cases',
    name: 'Cases',
    component: () => import('@/views/Cases.vue'),
    meta: { requiresAuth: true, title: '案例库' }
  },
  {
    path: '/sellers',
    name: 'Sellers',
    component: () => import('@/views/Sellers.vue'),
    meta: { requiresAuth: true, title: '商家管理', roles: ['admin'] }
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: () => import('@/views/Statistics.vue'),
    meta: { requiresAuth: true, title: '数据统计', roles: ['admin', 'arbitrator'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(userStore.currentUser?.role)) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
