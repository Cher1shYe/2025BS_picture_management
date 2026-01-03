<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getToken } from "@/utils/auth";
import axios from "axios";
// 引入图标
import {
  VideoPlay,
  VideoPause,
  FullScreen,
  CloseBold
} from "@element-plus/icons-vue";

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

// 打开轮播
const openCarousel = (index: number) => {
  initialIndex.value = index;
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
});
</script>

<template>
  <div class="gallery-container p-4">
    <div class="mb-4 flex justify-between items-center">
      <h2 class="text-xl font-bold text-gray-700">🖼️ 沉浸式画廊 (Gallery)</h2>
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
    <div
      v-if="showCarousel"
      class="fixed inset-0 z-50 bg-black flex flex-col justify-center"
    >
      <!-- 主要退出按钮 - 居中上方，更明显的位置 -->
      <div
        class="absolute top-8 left-1/2 -translate-x-1/2 z-[60] flex items-center gap-4 bg-black/50 backdrop-blur-sm px-6 py-3 rounded-full shadow-2xl hover:bg-black/70 transition-all duration-300"
        @click="closeCarousel"
      >
        <!-- 退出图标 -->
        <el-icon size="24" color="#fff">
          <CloseBold />
        </el-icon>
        <!-- 退出文字提示 -->
        <span class="text-white font-semibold text-lg">退出播放模式</span>
        <!-- ESC 提示 -->
        <span class="text-white/80 text-sm ml-2">(或按 Esc 键)</span>
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
