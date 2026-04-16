<template>
  <div class="login-page">
    <div class="main-box">
      <!-- 注册 -->
      <div :class="['container', 'container-register', { 'is-txl': isLogin }]">
        <form @submit.prevent="handleRegister">
          <h2 class="title">注册</h2>
          <span class="text">请输入注册信息</span>

          <input
              v-model.trim="registerForm.username"
              class="form__input"
              type="text"
              placeholder="请输入用户名"
          />
          <input
              v-model.trim="registerForm.mobile"
              class="form__input"
              type="tel"
              placeholder="请输入电话号码"
          />
          <input
              v-model="registerForm.password"
              class="form__input"
              type="password"
              placeholder="请输入密码"
          />
          <!-- 密码强度提示 -->
          <div class="password-strength" v-if="registerForm.password">
            <span :class="getStrengthClass()">密码强度：{{ getStrengthText() }}</span>
          </div>
          <input
              v-model="registerForm.rePassword"
              class="form__input"
              type="password"
              placeholder="请再次输入密码"
          />

          <button class="form__button" type="submit" :disabled="registerLoading">
            {{ registerLoading ? '注册中...' : '立即注册' }}
          </button>
        </form>
      </div>

      <!-- 登录（保持不变） -->
      <div :class="['container', 'container-login', { 'is-txl is-z200': isLogin }]">
        <form @submit.prevent="handleLogin">
          <h2 class="title">登录</h2>
          <span class="text">使用用户名/邮箱/手机号登录</span>

          <input
              v-model.trim="loginForm.username"
              class="form__input"
              type="text"
              placeholder="用户名/邮箱/手机号"
          />
          <input
              v-model="loginForm.password"
              class="form__input"
              type="password"
              placeholder="请输入密码"
          />

          <div class="captcha-wrap">
            <input
                v-model.trim="loginForm.captcha"
                class="form__input captcha-input"
                type="text"
                maxlength="4"
                placeholder="请输入验证码"
            />
            <img
                v-if="loginForm.captchaImgBase"
                class="captcha-img"
                :src="loginForm.captchaImgBase"
                alt="验证码"
                @click="refreshCaptcha"
            />
          </div>

          <button class="form__button" type="submit" :disabled="loginLoading">
            {{ loginLoading ? '登录中...' : '立即登录' }}
          </button>
          <div class="forgot-link" @click="router.push('/forgot-password')">忘记密码？</div>
        </form>

      </div>

      <!-- 中间切换区 -->
      <div :class="['switch', { login: isLogin }]">
        <div class="switch__circle"></div>
        <div class="switch__circle switch__circle_top"></div>
        <div class="switch__container">
          <h2>{{ isLogin ? '您好 !' : '欢迎回来 !' }}</h2>
          <p>
            {{
              isLogin
                  ? '如果您还没有账号，请点击下方立即注册按钮进行账号注册'
                  : '如果您已经注册过账号，请点击下方立即登录按钮进行登录'
            }}
          </p>
          <div class="form__button" @click="isLogin = !isLogin">
            {{ isLogin ? '立即注册' : '立即登录' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCaptcha, login, register } from '@/api/auth'
import { setAccessToken, setRefreshToken } from '@/utils/auth'

const router = useRouter()

const isLogin = ref(true)
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  captcha: '',
  captchaKey: '' as string | number,
  captchaImgBase: '',
})

const registerForm = reactive({
  username: '',
  mobile: '',
  password: '',
  rePassword: '',
})

// 强密码正则：至少8位，包含大小写字母、数字、特殊字符
const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/

// 计算密码强度得分（0~5）
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

// 获取强度文本
function getStrengthText(): string {
  const score = getPasswordStrength(registerForm.password)
  if (score < 3) return '弱'
  if (score < 5) return '中'
  return '强'
}
const mobileRegex = /^1[3-9]\d{9}$/

// 获取强度样式类
function getStrengthClass(): string {
  const score = getPasswordStrength(registerForm.password)
  if (score < 3) return 'weak'
  if (score < 5) return 'medium'
  return 'strong'
}

async function loadCaptcha() {
  try {
    const res = await getCaptcha()
    loginForm.captchaImgBase = res.data.data.image_base
    loginForm.captchaKey = res.data.data.key
    loginForm.captcha = ''
  } catch (error) {
    ElMessage.error('获取验证码失败')
  }
}

function refreshCaptcha() {
  loadCaptcha()
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password || !loginForm.captcha) {
    ElMessage.warning('请完整填写登录信息')
    return
  }

  loginLoading.value = true
  try {
    const res = await login({
      username: loginForm.username,
      password: loginForm.password,
      captcha: loginForm.captcha,
      captchaKey: loginForm.captchaKey,
    })

    const result = res.data
    if (result.code !== 2000) {
      ElMessage.error(result.msg || '登录失败')
      refreshCaptcha()
      return
    }

    const data = result.data
    setAccessToken(data.access)
    setRefreshToken(data.refresh)
    ElMessage.success(`登录成功，欢迎你：${data.name || data.username}`)
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '登录失败')
    refreshCaptcha()
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  // 非空校验
  if (
      !registerForm.username ||
      !registerForm.mobile ||
      !registerForm.password ||
      !registerForm.rePassword
  ) {
    ElMessage.warning('请完整填写注册信息')
    return
  }

  // 手机号格式校验
  if (!mobileRegex.test(registerForm.mobile)) {
    ElMessage.warning('请输入正确的手机号（11位数字，以1开头）')
    return
  }


  // 密码一致性校验
  if (registerForm.password !== registerForm.rePassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  // 强密码校验
  if (!strongPasswordRegex.test(registerForm.password)) {
    ElMessage.warning('密码必须包含大小写字母、数字和特殊字符，且长度至少8位')
    return
  }

  registerLoading.value = true
  try {
    const res = await register({
      username: registerForm.username,
      mobile: registerForm.mobile,
      password: registerForm.password,
      rePassword: registerForm.rePassword,
    })

    const result = res.data
    if (result.code !== 2000) {
      ElMessage.error(result.msg || '注册失败')
      return
    }

    ElMessage.success(result.msg || '注册成功，请登录')

    // 注册成功后切回登录页，并自动填入用户名
    isLogin.value = true
    loginForm.username = registerForm.username

    registerForm.username = ''
    registerForm.mobile = ''
    registerForm.password = ''
    registerForm.rePassword = ''
    refreshCaptcha()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '注册失败')
  } finally {
    registerLoading.value = false
  }
}

onMounted(() => {
  loadCaptcha()
})
</script>

<style scoped lang="scss">
.login-page {
  position: fixed;
  inset: 0;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #eef6ff 100%);
  background-image: url('@/assets/images/backgroud.jpg');
  font-family: "Montserrat", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #a0a5a8;
}

.main-box {
  position: relative;
  width: min(1000px, calc(100vw - 48px));
  height: min(600px, calc(100vh - 48px));
  background-color: #ecf0f3;
  box-shadow: 0 20px 60px rgba(88, 116, 173, 0.18);
  border-radius: 12px;
  overflow: hidden;
}

.container {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  width: min(600px, 100%);
  height: 100%;
  padding: 25px;
  background-color: #ecf0f3;
  transition: all 1.25s;

  form {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    min-width: 320px;
    width: 100%;
    max-width: 420px;
    height: 100%;
    color: #a0a5a8;
  }
}

.title {
  font-size: 34px;
  font-weight: 700;
  line-height: 2.5;
  color: #181818;
}

.text {
  margin-top: 10px;
  margin-bottom: 18px;
}
.forgot-link {
  margin-top: 12px;
  color: #4b70e2;
  cursor: pointer;
  text-align: center;
}
.form__input {
  width: 100%;
  height: 44px;
  margin: 6px 0;
  padding: 0 18px;
  font-size: 13px;
  letter-spacing: 0.15px;
  border: none;
  outline: none;
  background-color: #ecf0f3;
  border-radius: 10px;
  box-shadow: inset 2px 2px 4px #d1d9e6, inset -2px -2px 4px #f9f9f9;
  box-sizing: border-box;
}

.password-strength {
  width: 100%;
  text-align: left;
  font-size: 12px;
  margin-top: -4px;
  margin-bottom: 6px;
  padding-left: 10px;

  .weak { color: #f56c6c; }
  .medium { color: #e6a23c; }
  .strong { color: #67c23a; }
}

.captcha-wrap {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 12px;
  align-items: center;
}

.captcha-input {
  margin: 0;
}

.captcha-img {
  width: 120px;
  height: 44px;
  border-radius: 10px;
  cursor: pointer;
  object-fit: cover;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.container-register {
  z-index: 100;
  left: calc(100% - min(600px, 100%));
}

.container-login {
  left: calc(100% - min(600px, 100%));
  z-index: 0;
}

.is-txl {
  left: 0;
  transition: 1.25s;
  transform-origin: right;
}

.is-z200 {
  z-index: 200;
  transition: 1.25s;
}

.switch {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  width: min(400px, 42%);
  height: 100%;
  padding: 50px;
  z-index: 200;
  transition: 1.25s;
  background-color: #ecf0f3;
  overflow: hidden;
  box-shadow: 4px 4px 10px #d1d9e6, -4px -4px 10px #f9f9f9;
  color: #a0a5a8;
  box-sizing: border-box;
}

.switch__circle {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background-color: #ecf0f3;
  box-shadow: inset 8px 8px 12px #d1d9e6, inset -8px -8px 12px #f9f9f9;
  bottom: -60%;
  left: -60%;
  transition: 1.25s;
}

.switch__circle_top {
  top: -30%;
  left: 60%;
  width: 300px;
  height: 300px;
}

.switch__container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: absolute;
  width: min(400px, 100%);
  padding: 50px 40px;
  transition: 1.25s;
  box-sizing: border-box;

  h2 {
    font-size: 34px;
    font-weight: 700;
    line-height: 2.5;
    color: #181818;
    margin: 0 0 12px;
  }

  p {
    font-size: 14px;
    letter-spacing: 0.25px;
    text-align: center;
    line-height: 1.6;
    margin: 0;
  }
}

.login {
  left: calc(100% - min(400px, 42%));

  .switch__circle {
    left: 0;
  }
}

.form__button {
  width: 180px;
  height: 50px;
  border-radius: 25px;
  margin-top: 28px;
  text-align: center;
  line-height: 50px;
  font-size: 14px;
  letter-spacing: 2px;
  background-color: #4b70e2;
  color: #f9f9f9;
  cursor: pointer;
  box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #f9f9f9;
  border: none;

  &:hover {
    box-shadow:
        2px 2px 3px 0 rgba(255, 255, 255, 50%),
        -2px -2px 3px 0 rgba(116, 125, 136, 50%),
        inset -2px -2px 3px 0 rgba(255, 255, 255, 20%),
        inset 2px 2px 3px 0 rgba(0, 0, 0, 30%);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
}
</style>