import axios from 'axios'
import md5 from 'blueimp-md5'
import { getAccessToken, clearToken } from '@/utils/auth'

const request = axios.create({
    baseURL: 'http://127.0.0.1:8000', // 改成你的 Django 后端地址
    timeout: 10000,
})

request.interceptors.request.use(
    (config) => {
        const token = getAccessToken()
        if (token&&config.headers) {
            config.headers.Authorization = `JWT ${token}`
        }
        return config
    },
    (error) => Promise.reject(error),
)

request.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            clearToken()
        }
        return Promise.reject(error)
    },
)

export interface LoginParams {
    username: string
    password: string
    captcha: string
    captchaKey: string | number
}

export interface LoginResponseData {
    access: string
    refresh: string
    username: string
    name: string
    userId: number
    avatar?: string
    user_type?: string | number
    pwd_change_count?: number
}

export interface RegisterResponseData {

}

export interface SendResetCodeParams {
    username: string
    mobile: string
}

export interface ResetForgotPasswordParams {
    username: string
    mobile: string
    code: string
    password: string
    rePassword: string
}

export interface RegisterParams {
    username: string
    mobile: string
    password: string
    rePassword: string
}

export interface ApiResponse<T = any> {
    code: number
    msg: string
    data: T
}

export interface ChangePasswordParams {
    oldPassword: string
    newPassword: string
    newPassword2: string
}

export interface UserInfo {
    id: number
    username: string
    name: string
    mobile: string
    avatar?: string
    email?: string
    gender: number
    user_type: number
    dept?: number
    role?: number[]
    pwd_change_count?: number
}


export function getCaptcha() {
    return request.get<ApiResponse<{ key: string | number; image_base: string }>>(
        '/api/captcha/',
    )
}

export function login(params: LoginParams) {
    return request.post<ApiResponse<LoginResponseData>>('/api/login/', {
        ...params,
        password: md5(params.password),
    })
}

export function register(params: RegisterParams) {
    return request.post<ApiResponse<RegisterResponseData>>('/api/register/', params)
}

export function logout() {
    return request.post<ApiResponse>('/api/logout/')
}

export function sendResetCode(params: SendResetCodeParams) {
    return request.post<ApiResponse>('/api/password/send_reset_code/', params)
}

export function resetForgotPassword(params: ResetForgotPasswordParams) {
    return request.post<ApiResponse>('/api/password/reset_by_code/', params)
}

export function changePassword(params: ChangePasswordParams) {
    return request.post<ApiResponse>('/api/change-password/', params)
}

export function getUserInfo() {
    return request.get<ApiResponse<UserInfo>>('/api/system/user/user_info/')
}
export default request