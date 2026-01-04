<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getToken } from "@/utils/auth";

import axios from "axios";
// 引入图标
import { VideoPlay, VideoPause, CloseBold } from "@element-plus/icons-vue";

defineOptions({ name: "GalleryMode" });

const imageList = ref([]);
const loading = ref(false);

// 轮播相关状态
const showCarousel = ref(false);
const initialIndex = ref(0);
const autoPlay = ref(false);
const carouselRef = ref(null);
let timer = null;

// 获取图片 (取前100张用于展示)
const getGalleryData = async () => {
  loading.value = true;
  try {
    const res = await axios.get("/api/image/list", {
      params: { page: 1, limit: 100 }, // 一次拿100张
      headers: { Authorization: "Bearer " + getToken()?.accessToken }
    });
    if (res.data.code === 200) {
      imageList.value = res.data.data.items;
    }
  } finally {
    loading.value = false;
  }
};

// --- 核心：控制 Pure Admin 布局全屏 ---
const toggleLayoutMaximize = (start: boolean) => {
  const app = document.getElementById("app");
  if (!app) return;
  if (start) {
    // 添加 main-maximize 类 -> 框架会自动隐藏 Sidebar 和 Navbar
    app.classList.add("main-maximize");
  } else {
    // 移除类 -> 恢复 Sidebar 和 Navbar
    app.classList.remove("main-maximize");
  }
};

// 打开轮播
const openCarousel = (index: number) => {
  initialIndex.value = index;
  toggleLayoutMaximize(true);
  showCarousel.value = true;
};

// 切换自动播放
const toggleAutoPlay = () => {
  autoPlay.value = !autoPlay.value;
  if (autoPlay.value) {
    startTimer();
  } else {
    stopTimer();
  }
};

const startTimer = () => {
  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    if (carouselRef.value) {
      carouselRef.value.next();
    }
  }, 3000); // 3秒切一张
};

const stopTimer = () => {
  if (timer) clearInterval(timer);
};

// 监听轮播改变 (如果手动切了，重置计时器)
const handleChange = () => {
  if (autoPlay.value) {
    startTimer(); // 重置倒计时
  }
};

// 关闭轮播
const closeCarousel = () => {
  showCarousel.value = false;
  stopTimer();
  autoPlay.value = false; // 关闭自动播放
  // 延迟一点点恢复，防止闪烁
  setTimeout(() => {
    toggleLayoutMaximize(false);
  }, 100);
};

// 键盘监听 (按 Esc 退出)
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === "Escape" && showCarousel.value) {
    closeCarousel();
  }
};

onMounted(() => {
  getGalleryData();
  window.addEventListener("keydown", handleKeydown); // 监听键盘
});

import { onUnmounted } from "vue";
onUnmounted(() => {
  stopTimer();
  window.removeEventListener("keydown", handleKeydown);
  // 离开页面时必须强制恢复布局，否则侧边栏会一直消失！
  toggleLayoutMaximize(false);
});
</script>

<template>
  <div class="gallery-container p-4">
    <div class="mb-4 flex justify-between items-center">
      <h2 class="text-xl font-bold text-gray-700">🖼️ 画廊模式 (Gallery)</h2>
      <el-button
        type="primary"
        size="large"
        :icon="VideoPlay"
        @click="openCarousel(0)"
      >
        开始全屏幻灯片播放
      </el-button>
    </div>

    <!-- 瀑布流/网格展示区 -->
    <div
      v-loading="loading"
      class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4"
    >
      <div
        v-for="(item, index) in imageList"
        :key="item.id"
        class="photo-item cursor-pointer relative group overflow-hidden rounded-lg shadow-md aspect-square"
        @click="openCarousel(index)"
      >
        <img
          :src="item.thumb || item.url"
          class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        <div
          class="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
        >
          <span class="text-white font-bold"
            ><el-icon><FullScreen /></el-icon
          ></span>
        </div>
      </div>
    </div>

    <!-- 全屏轮播层 (Overlay) -->
    <!-- z-index 设高一点，遮盖住面包屑等可能残留的元素 -->
    <div
      v-if="showCarousel"
      class="fixed inset-0 z-[9999] bg-black flex flex-col justify-center"
      style="margin: 0 !important; top: 0; left: 0; width: 100vw; height: 100vh"
    >
      <!-- 顶部控制栏 -->
      <div
        class="absolute top-0 left-0 right-0 z-[10000] flex justify-between items-center p-6 bg-gradient-to-b from-black/80 to-transparent"
      >
        <div class="text-white/80 font-mono">
          {{ initialIndex + 1 }} / {{ imageList.length }}
        </div>
        <div
          class="cursor-pointer bg-white/10 hover:bg-white/20 p-2 rounded-full transition-all flex items-center gap-2 px-4"
          @click="closeCarousel"
        >
          <span class="text-white text-sm">退出播放(或按Esc退出)</span>
          <el-icon size="20" color="#fff"><CloseBold /></el-icon>
        </div>
      </div>
      <!-- 自动播放控制器 -->
      <div class="absolute bottom-10 left-1/2 -translate-x-1/2 z-50 flex gap-4">
        <el-button
          round
          :type="autoPlay ? 'warning' : 'success'"
          @click="toggleAutoPlay"
        >
          <el-icon class="mr-1"
            ><component :is="autoPlay ? VideoPause : VideoPlay"
          /></el-icon>
          {{ autoPlay ? "停止播放" : "自动播放 (3s)" }}
        </el-button>
      </div>

      <!-- Carousel 组件 -->
      <el-carousel
        ref="carouselRef"
        :initial-index="initialIndex"
        height="100vh"
        indicator-position="none"
        arrow="always"
        :autoplay="false"
        @change="handleChange"
      >
        <el-carousel-item v-for="item in imageList" :key="item.id">
          <div class="w-full h-full flex items-center justify-center">
            <img :src="item.url" class="max-w-full max-h-full object-contain" />
            <!-- 图片信息字幕 -->
            <div
              class="absolute bottom-24 bg-black/50 px-4 py-2 rounded text-white text-center"
            >
              >
              <div class="text-lg font-bold">{{ item.name }}</div>
              <div class="text-sm text-gray-300">
                {{ item.date }} · {{ item.location }}
              </div>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>
  </div>
</template>

<style scoped>
.photo-item {
  /* 简单的 hover 动效 */
  transition: all 0.3s;
}
/* 隐藏 Element Carousel 默认的背景色 */
:deep(.el-carousel__item) {
  background: black;
}
</style>
