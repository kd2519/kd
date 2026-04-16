<template>
  <div class="forgot-page">
    <div class="forgot-card">
      <h2 class="title">找回密码</h2>
      <p class="sub-title">请输入账号手机号并完成验证码验证</p>

      <div class="form-item">
        <input v-model.trim="form.username" class="form__input" type="text" placeholder="请输入用户名" />
      </div>

      <div class="form-item">
        <input v-model.trim="form.mobile" class="form__input" type="tel" placeholder="请输入手机号" />
      </div>

      <div class="form-item code-row">
        <input v-model.trim="form.code" class="form__input code-input" type="text" placeholder="请输入短信验证码" />
        <button class="code-btn" :disabled="countdown > 0 || sendLoading" @click="handleSendCode">
          {{ countdown > 0 ? `${countdown}s后重发` : (sendLoading ? '发送中...' : '发送验证码') }}
        </button>
      </div>

      <div class="form-item">
        <input v-model="form.password" class="form__input" type="password" placeholder="请输入新密码" />
        <div class="password-strength" v-if="form.password">
          <span :class="getStrengthClass()">密码强度：{{ getStrengthText() }}</span>
        </div>
      </div>

      <div class="form-item">
        <input v-model="form.rePassword" class="form__input" type="password" placeholder="请再次输入新密码" />
      </div>

      <button class="submit-btn" :disabled="submitLoading" @click="handleResetPassword">
        {{ submitLoading ? '提交中...' : '重置密码' }}
      </button>

      <div class="back-login" @click="goLogin">返回登录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { sendResetCode, resetForgotPassword } from '@/api/auth'

const router = useRouter()

const sendLoading = ref(false)
const submitLoading = ref(false)
const countdown = ref(0)
let timer: number | null = null

const form = reactive({
  username: '',
  mobile: '',
  code: '',
  password: '',
  rePassword: '',
})

// 强密码正则（与注册一致）
const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/

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
  const score = getPasswordStrength(form.password)
  if (score < 3) return '弱'
  if (score < 5) return '中'
  return '强'
}

function getStrengthClass(): string {
  const score = getPasswordStrength(form.password)
  if (score < 3) return 'weak'
  if (score < 5) return 'medium'
  return 'strong'
}

function startCountdown() {
  countdown.value = 60
  timer = window.setInterval(() => {
    countdown.value--
    if (countdown.value <= 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

async function handleSendCode() {
  if (!form.username || !form.mobile) {
    ElMessage.warning('请先填写用户名和手机号')
    return
  }

  sendLoading.value = true
  try {
    const res = await sendResetCode({
      username: form.username,
      mobile: form.mobile,
    })
    const result = res.data
    if (result.code !== 2000) {
      ElMessage.error(result.msg || '验证码发送失败')
      return
    }
    ElMessage.success(result.msg || '验证码已发送')
    startCountdown()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '验证码发送失败')
  } finally {
    sendLoading.value = false
  }
}

async function handleResetPassword() {
  if (!form.username || !form.mobile || !form.code || !form.password || !form.rePassword) {
    ElMessage.warning('请完整填写信息')
    return
  }

  if (form.password !== form.rePassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  if (!strongPasswordRegex.test(form.password)) {
    ElMessage.warning('密码必须包含大小写字母、数字和特殊字符，且长度至少8位')
    return
  }

  submitLoading.value = true
  try {
    const res = await resetForgotPassword({
      username: form.username,
      mobile: form.mobile,
      code: form.code,
      password: form.password,
      rePassword: form.rePassword,
    })
    const result = res.data
    if (result.code !== 2000) {
      ElMessage.error(result.msg || '重置失败')
      return
    }

    ElMessage.success(result.msg || '密码重置成功，请重新登录')
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '重置失败')
  } finally {
    submitLoading.value = false
  }
}

function goLogin() {
  router.push('/login')
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.forgot-page {
  position: fixed;
  inset: 0;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #eef6ff 100%);
  background-image: url('@/assets/images/backgroud.jpg');
  font-family: "Montserrat", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.forgot-card {
  width: 100%;
  max-width: 460px;
  background-color: #ecf0f3;
  border-radius: 28px;
  padding: 40px 32px 48px;
  box-shadow: 0 20px 40px rgba(88, 116, 173, 0.12), 8px 8px 20px rgba(0, 0, 0, 0.05), -8px -8px 20px rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;

  .title {
    font-size: 32px;
    font-weight: 700;
    text-align: center;
    color: #181818;
    margin: 0 0 8px;
    letter-spacing: -0.3px;
  }

  .sub-title {
    text-align: center;
    color: #8a93a0;
    font-size: 14px;
    margin-bottom: 32px;
  }

  .form-item {
    margin-bottom: 20px;
  }

  .form__input {
    width: 100%;
    height: 48px;
    padding: 0 18px;
    font-size: 14px;
    border: none;
    outline: none;
    background-color: #ecf0f3;
    border-radius: 14px;
    box-shadow: inset 2px 2px 5px #d1d9e6, inset -3px -3px 7px #ffffff;
    transition: 0.2s;
    font-family: inherit;
    box-sizing: border-box;

    &:focus {
      box-shadow: inset 3px 3px 6px #d1d9e6, inset -2px -2px 5px #ffffff;
    }
  }

  .code-row {
    display: flex;
    gap: 12px;
    align-items: center;

    .code-input {
      flex: 1;
    }

    .code-btn {
      width: 110px;
      height: 48px;
      border-radius: 14px;
      background-color: #ecf0f3;
      border: none;
      font-size: 13px;
      font-weight: 500;
      color: #4b70e2;
      cursor: pointer;
      box-shadow: 5px 5px 12px #d1d9e6, -3px -3px 8px #ffffff;
      transition: all 0.2s;
      white-space: nowrap;

      &:hover:not(:disabled) {
        box-shadow: 2px 2px 6px #d1d9e6, -2px -2px 5px #ffffff;
        color: #3a5bc0;
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        color: #8e9aaf;
      }
    }
  }

  .password-strength {
    font-size: 12px;
    margin-top: 6px;
    padding-left: 12px;
    .weak { color: #f56c6c; }
    .medium { color: #e6a23c; }
    .strong { color: #67c23a; }
  }

  .submit-btn {
    width: 100%;
    height: 52px;
    border-radius: 28px;
    background-color: #4b70e2;
    border: none;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 1px;
    color: white;
    cursor: pointer;
    box-shadow: 6px 6px 14px #d1d9e6, -4px -4px 10px #ffffff;
    transition: all 0.2s;
    margin-top: 12px;
    margin-bottom: 24px;

    &:hover:not(:disabled) {
      background-color: #3f64d0;
      transform: translateY(-1px);
      box-shadow: 8px 8px 18px #d1d9e6, -4px -4px 10px #ffffff;
    }

    &:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
  }

  .back-login {
    text-align: center;
    font-size: 14px;
    color: #4b70e2;
    cursor: pointer;
    transition: 0.2s;

    &:hover {
      color: #2f4faf;
      text-decoration: underline;
    }
  }
}

/* 移动端适配 */
@media (max-width: 560px) {
  .forgot-card {
    padding: 32px 24px;
  }
  .code-row {
    flex-wrap: wrap;
    .code-btn {
      width: 100%;
    }
  }
}
</style>