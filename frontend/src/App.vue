<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <el-header v-if="userStore.isLoggedIn" class="app-header">
        <div class="header-left">
          <el-text class="logo" type="primary" size="large">
            <el-icon :size="24"><ShoppingCart /></el-icon>
            智能电商维权平台
          </el-text>
        </div>
        <div class="header-right">
          <el-text>{{ userStore.currentUser?.name }}</el-text>
          <el-tag :type="userStore.currentUser?.role === 'admin' ? 'danger' : 'primary'">
            {{ getRoleText(userStore.currentUser?.role) }}
          </el-tag>
          <el-button type="text" @click="logout">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const getRoleText = (role) => {
  const roleMap = {
    buyer: '买家',
    seller: '卖家',
    admin: '平台管理员',
    arbitrator: '仲裁员'
  }
  return roleMap[role] || role
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  color: white !important;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
  color: white;
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.el-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}
</style>
