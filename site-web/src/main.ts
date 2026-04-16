import './style.css';
import 'element-plus/dist/index.css';

import { createApp } from 'vue';

import ElementPlus from 'element-plus';

import * as ElementPlusIconsVue from '@element-plus/icons-vue';

import App from './App.vue';
import router from './router';
import pinia from './stores';

const app = createApp(App)
//注册elementplus
app.use(ElementPlus)
//注册elementplus的图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}
//注册pinia
app.use(pinia);
app.use(router)

app.mount('#app')