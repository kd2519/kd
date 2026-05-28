<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <div class="navbar">
      <div class="logo">demo</div>
      <div class="user-info">
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="avatar-wrapper">
            <el-avatar :src="userInfo.avatar || defaultAvatar" :size="40" />
            <span class="username">{{ userInfo.name || userInfo.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePassword">
                <el-icon><Key /></el-icon> 修改密码
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主体内容（可保留原有卡片风格） -->
    <div class="main-content">
      <div class="welcome-card">
        <h2>欢迎回来，{{ userInfo.name || userInfo.username }}！</h2>
        <p>你已经登录成功，可以开始使用了。</p>
        <el-button type="primary" @click="goToEeg" style="margin-top: 20px;">
          进入 EEG 睡眠分析系统
        </el-button>
      </div>
    </div>

    <!-- 修改密码弹窗（保持不变） -->
    <el-dialog
        v-model="dialogVisible"
        title="修改密码"
        width="30%"
        @close="resetForm"
    >
      <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
              v-model="form.oldPassword"
              type="password"
              show-password
              placeholder="请输入旧密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
              v-model="form.newPassword"
              type="password"
              show-password
              placeholder="请输入新密码"
          />
          <div class="password-strength" v-if="form.newPassword">
            <span :class="getStrengthClass()">强度：{{ getStrengthText() }}</span>
          </div>
        </el-form-item>
        <el-form-item label="确认新密码" prop="newPassword2">
          <el-input
              v-model="form.newPassword2"
              type="password"
              show-password
              placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChangePassword" :loading="loading">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { ArrowDown, Key, SwitchButton } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { logout, changePassword, getUserInfo,type UserInfo } from '@/api/auth'
import { clearToken } from '@/utils/auth'
import defaultAvatar from '@/assets/images/avatar.jpg' // 可准备一个默认头像

const router = useRouter()


const goToEeg = () => {
  router.push('/eeg')
}
// 用户信息
const userInfo = ref<UserInfo>({
  id: 0,
  username: '',
  name: '',
  mobile: '',
  avatar: '',
  email: '',
  gender: 0,
  user_type: 0,
  pwd_change_count: 0
})

// 获取当前用户信息
const fetchUserInfo = async () => {
  try {
    const res = await getUserInfo()
    if (res.data.code === 2000) {
      userInfo.value = res.data.data
    }
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

// 下拉菜单命令处理
const handleCommand = (command: string) => {
  if (command === 'changePassword') {
    openChangePasswordDialog()
  } else if (command === 'logout') {
    handleLogout()
  }
}

// 修改密码弹窗相关
const dialogVisible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  newPassword2: ''
})

const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/

const validateNewPassword = (_rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入新密码'))
  } else if (!strongPasswordRegex.test(value)) {
    callback(new Error('密码必须包含大小写字母、数字和特殊字符，且长度至少8位'))
  } else {
    callback()
  }
}

const validateConfirm = (_rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
  } else if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [{ validator: validateNewPassword, trigger: 'blur' }],
  newPassword2: [{ validator: validateConfirm, trigger: 'blur' }]
}

function getPasswordStrength(pwd: string): number {
  if (!pwd) return 0
  let score = 0
  if (pwd.length >= 8) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[@$!%*?&]/.test(pwd)) score++
  return score
}

function getStrengthText(): string {
  const score = getPasswordStrength(form.newPassword)
  if (score < 3) return '弱'
  if (score < 5) return '中'
  return '强'
}

function getStrengthClass(): string {
  const score = getPasswordStrength(form.newPassword)
  if (score < 3) return 'weak'
  if (score < 5) return 'medium'
  return 'strong'
}

function openChangePasswordDialog() {
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  form.oldPassword = ''
  form.newPassword = ''
  form.newPassword2 = ''
}

async function submitChangePassword() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await changePassword({
        oldPassword: form.oldPassword,
        newPassword: form.newPassword,
        newPassword2: form.newPassword2
      })
      if (res.data.code === 2000) {
        ElMessage.success('密码修改成功，请重新登录')
        dialogVisible.value = false
        // 修改成功后可选择自动退出登录
        await handleLogout()
      } else {
        ElMessage.error(res.data.msg || '修改失败')
      }
    } catch (error: any) {
      ElMessage.error(error?.response?.data?.msg || error?.message || '修改失败')
    } finally {
      loading.value = false
    }
  })
}

async function handleLogout() {
  try {
    await logout()
  } catch (error) {
    // ignore
  } finally {
    clearToken()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped lang="scss">
.home-page {
  min-height: 100vh;
  background: #f0f2f6;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.navbar {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;

  .logo {
    font-size: 20px;
    font-weight: 500;
    color: #2c3e50;
  }

  .user-info {
    .avatar-wrapper {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      .username {
        font-size: 14px;
        color: #333;
      }
      .el-icon {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

/* 主体内容 */
.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.welcome-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 60px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  text-align: center;
  max-width: 600px;

  h2 {
    margin-bottom: 16px;
    color: #2c3e50;
  }
  p {
    color: #7f8c8d;
    font-size: 16px;
  }
}

/* 密码强度样式 */
.password-strength {
  font-size: 12px;
  margin-top: 4px;
  text-align: left;
}
.weak { color: #f56c6c; }
.medium { color: #e6a23c; }
.strong { color: #67c23a; }
</style>