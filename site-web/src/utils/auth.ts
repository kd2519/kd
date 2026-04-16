// src/utils/auth.ts
export function setAccessToken(token: string) {
    localStorage.setItem('site_access_token', token)
}

export function getAccessToken() {
    return localStorage.getItem('site_access_token')
}

export function setRefreshToken(token: string) {
    localStorage.setItem('site_refresh_token', token)
}

export function getRefreshToken() {
    return localStorage.getItem('site_refresh_token')
}

export function clearToken() {
    localStorage.removeItem('site_access_token')
    localStorage.removeItem('site_refresh_token')
}