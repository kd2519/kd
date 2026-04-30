<template>
  <header class="header">
    <div class="logo-wrap">
      <div class="logo-ring">
        <div class="logo-container">
          <img src="/logo.jpg" alt="云梦泽 - Yun Meng Ze">
        </div>
      </div>
    </div>
    <h1 class="title">基于EEG与人工智能的睡眠健康评估系统 V2.0</h1>
    <p class="subtitle">实时采集 · 本地存储 · 智能分析</p>
    <div class="header-accent" aria-hidden="true"></div>
  </header>
</template>

<script>
export default {
  name: 'EEGHomePageHeader',
};
</script>

<style scoped>
.header {
  text-align: center;
  margin-bottom: 26px;
  padding-bottom: 22px;
}
.header-accent {
  width: min(420px, 70vw);
  height: 2px;
  margin: 18px auto 0;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(59, 130, 246, 0.35) 20%,
    rgba(226, 232, 240, 0.45) 50%,
    rgba(59, 130, 246, 0.35) 80%,
    transparent
  );
  opacity: 0.9;
}
.logo-wrap {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}
.logo-ring {
  padding: 3px;
  border-radius: 50%;
  background: linear-gradient(145deg, rgba(148, 163, 184, 0.5), rgba(30, 41, 59, 0.8), rgba(59, 130, 246, 0.35));
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.06),
    0 12px 40px rgba(15, 23, 42, 0.45);
}
.logo-container {
  width: 120px;
  height: 120px;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.65);
}
.logo-container img {
  width: 112px;
  height: auto;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  border: none;
  display: block;
}
.title {
  color: #f4e4a8;
  font-size: clamp(1.15rem, 2.8vw, 1.65rem);
  font-weight: 600;
  letter-spacing: 0.02em;
  margin: 16px 16px 8px;
  line-height: 1.35;
  text-shadow: 0 2px 16px rgba(15, 23, 42, 0.55);
}
.subtitle {
  color: #94a3b8;
  font-size: 0.8125rem;
  margin-top: 2px;
  letter-spacing: 0.12em;
}
</style>
