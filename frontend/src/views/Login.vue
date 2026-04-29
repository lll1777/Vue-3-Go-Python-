<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="32" color="#409eff"><ShoppingCart /></el-icon>
          <h2>智能电商维权仲裁平台</h2>
        </div>
      </template>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="80px"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="loginForm.role" placeholder="选择角色" size="large" style="width: 100%">
            <el-option label="买家" value="buyer" />
            <el-option label="卖家" value="seller" />
            <el-option label="仲裁员" value="arbitrator" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="demo-users">
        <el-text type="info" size="small">演示账号：</el-text>
        <div class="user-list">
          <el-tag size="small" @click="fillUser('buyer1', 'buyer')">买家: buyer1</el-tag>
          <el-tag size="small" @click="fillUser('seller1', 'seller')">卖家: seller1</el-tag>
          <el-tag size="small" @click="fillUser('admin1', 'admin')">管理员: admin1</el-tag>
          <el-tag size="small" @click="fillUser('arbitrator1', 'arbitrator')">仲裁员: arbitrator1</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const loginFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: '123456',
  role: 'buyer'
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm)
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        ElMessage.error('登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}

const fillUser = (username, role) => {
  loginForm.username = username
  loginForm.role = role
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.card-header h2 {
  margin: 0;
  color: #409eff;
}

.login-form {
  margin-top: 20px;
}

.login-btn {
  width: 100%;
}

.demo-users {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.user-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.user-list .el-tag {
  cursor: pointer;
}
</style>
