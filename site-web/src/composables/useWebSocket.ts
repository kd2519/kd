import { ref, onUnmounted } from 'vue'

export function useWebSocket(url: string) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const lastMessage = ref<any>(null)

  const connect = () => {
    if (socket.value?.readyState === WebSocket.OPEN) return
    socket.value = new WebSocket(url)
    socket.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }
    socket.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }
    socket.value.onerror = (err) => {
      console.error('WebSocket error', err)
    }
  }

  const send = (data: any) => {
    if (socket.value?.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  const onMessage = (callback: (data: any) => void) => {
    if (socket.value) {
      socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        lastMessage.value = data
        callback(data)
      }
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return { connect, send, onMessage, disconnect, isConnected, lastMessage }
}