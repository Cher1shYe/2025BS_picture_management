<template>
  <el-dialog
    v-model="dialogVisible"
    title="🪄 图片编辑 (裁剪 & 调色)"
    width="900px"
    :close-on-click-modal="false"
    append-to-body
    destroy-on-close
  >
    <div class="flex h-[500px] gap-4">
      <!-- 左侧：编辑区 加上 crossorigin="anonymous"-->
      <div
        class="flex-1 bg-black/90 flex items-center justify-center overflow-hidden relative rounded-lg border border-gray-700"
      >
        <img
          ref="imageRef"
          :src="imageUrl"
          crossorigin="anonymous"
          class="max-w-full"
          style="display: block; max-width: 100%"
        />
      </div>

      <!-- 右侧：控制面板 -->
      <div class="w-72 flex flex-col gap-6 p-2 overflow-y-auto">
        <!-- 1. 裁剪预设 -->
        <div>
          <div class="text-sm font-bold mb-2 text-gray-600">📐 裁剪比例</div>
          <div class="grid grid-cols-3 gap-2">
            <el-button size="small" @click="setRatio(NaN)">自由</el-button>
            <el-button size="small" @click="setRatio(1)">1:1</el-button>
            <el-button size="small" @click="setRatio(16 / 9)">16:9</el-button>
            <el-button size="small" @click="setRatio(4 / 3)">4:3</el-button>
          </div>
        </div>

        <!-- 2. 旋转 & 翻转 -->
        <div>
          <div class="text-sm font-bold mb-2 text-gray-600">🔄 旋转与翻转</div>
          <div class="flex gap-2 justify-between">
            <el-button-group>
              <el-button size="small" @click="rotate(-90)">↺</el-button>
              <el-button size="small" @click="rotate(90)">↻</el-button>
            </el-button-group>
            <el-button-group>
              <el-button size="small" @click="scaleX">↔</el-button>
              <el-button size="small" @click="scaleY">↕</el-button>
            </el-button-group>
          </div>
        </div>

        <!-- 3. 色调调整 (滤镜) -->
        <div>
          <div class="text-sm font-bold mb-2 text-gray-600">🎨 色调调整</div>

          <div class="mb-2">
            <span class="text-xs text-gray-500"
              >亮度 ({{ filters.brightness }}%)</span
            >
            <el-slider
              v-model="filters.brightness"
              :min="0"
              :max="200"
              size="small"
              @input="applyFilter"
            />
          </div>

          <div class="mb-2">
            <span class="text-xs text-gray-500"
              >对比度 ({{ filters.contrast }}%)</span
            >
            <el-slider
              v-model="filters.contrast"
              :min="0"
              :max="200"
              size="small"
              @input="applyFilter"
            />
          </div>

          <div class="mb-2">
            <span class="text-xs text-gray-500"
              >饱和度 ({{ filters.saturate }}%)</span
            >
            <el-slider
              v-model="filters.saturate"
              :min="0"
              :max="200"
              size="small"
              @input="applyFilter"
            />
          </div>

          <el-button link type="primary" size="small" @click="resetFilters"
            >重置滤镜</el-button
          >
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <span class="text-xs text-gray-400">编辑后的图片将保存为新文件</span>
        <div>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave"
            >保存新图片</el-button
          >
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, watch } from "vue";
import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import axios from "axios";
import { getToken } from "@/utils/auth";
import { message } from "@/utils/message";

const props = defineProps<{
  refreshList?: () => void; // 保存成功后刷新列表的回调
}>();

const dialogVisible = ref(false);
const imageUrl = ref("");
const imageRef = ref<HTMLImageElement | null>(null);
const saving = ref(false);
let cropper: Cropper | null = null;

// 滤镜参数
const filters = reactive({
  brightness: 100,
  contrast: 100,
  saturate: 100
});

// 翻转状态
let scaleXVal = 1;
let scaleYVal = 1;

// 打开弹窗的方法（供父组件调用）
const open = (url: string) => {
  //TODO：加入时间戳防止读缓存？
  const timestamp = new Date().getTime();
  imageUrl.value = `${url}${url.includes("?") ? "&" : "?"}t=${timestamp}`;
  dialogVisible.value = true;
  // 重置状态
  resetFilters();
  scaleXVal = 1;
  scaleYVal = 1;
  // 等待 DOM 渲染后初始化 Cropper
  nextTick(() => {
    initCropper();
  });
};

// 初始化 Cropper
const initCropper = () => {
  if (cropper) {
    cropper.destroy();
  }
  if (imageRef.value) {
    cropper = new Cropper(imageRef.value, {
      viewMode: 1, // 限制裁剪框不能超出图片
      dragMode: "move",
      background: false,
      autoCropArea: 0.8,
      checkCrossOrigin: false // 避免跨域问题
    });
  }
};

// 操作方法
const setRatio = (ratio: number) => cropper?.setAspectRatio(ratio);
const rotate = (deg: number) => cropper?.rotate(deg);
const scaleX = () => {
  scaleXVal = -scaleXVal;
  cropper?.scaleX(scaleXVal);
};
const scaleY = () => {
  scaleYVal = -scaleYVal;
  cropper?.scaleY(scaleYVal);
};

// 实时滤镜预览 (通过 CSS 简单模拟，提升性能)
const applyFilter = () => {
  // 注意：CropperJS 只是裁剪，它不会实时把滤镜渲染到 Canvas 内部
  // 这里我们给 img 加 css filter 只是为了视觉预览
  // 真正保存时，我们需要手动画到 Canvas 上
  const filterStr = `brightness(${filters.brightness}%) contrast(${filters.contrast}%) saturate(${filters.saturate}%)`;
  // Cropper 会在图片外面包一层 container，我们需要给那个 container 加滤镜
  const container = document.querySelector(
    ".cropper-container .cropper-canvas"
  ) as HTMLElement;
  if (container) {
    container.style.filter = filterStr;
  }
  // 同时也给预览图加
  const wrap = document.querySelector(
    ".cropper-container .cropper-view-box img"
  ) as HTMLElement;
  if (wrap) {
    wrap.style.filter = filterStr;
  }
};

const resetFilters = () => {
  filters.brightness = 100;
  filters.contrast = 100;
  filters.saturate = 100;
  applyFilter();
};

// 保存核心逻辑
const handleSave = () => {
  if (!cropper) return;
  saving.value = true;

  // 1. 获取裁剪后的 Canvas
  const canvas = cropper.getCroppedCanvas({
    fillColor: "#fff" // 填充透明背景为白色(如果是jpg)
  });

  // 2. 处理滤镜 (这是最关键的一步)
  // 因为 Cropper 只是裁剪，滤镜是我们用 CSS 加上去的，所以我们需要手动把滤镜画到 Canvas 上
  const ctx = canvas.getContext("2d");
  if (ctx) {
    // 创建一个新的临时 Canvas 来应用滤镜
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    const tempCtx = tempCanvas.getContext("2d");

    if (tempCtx) {
      // 设置滤镜字符串
      tempCtx.filter = `brightness(${filters.brightness}%) contrast(${filters.contrast}%) saturate(${filters.saturate}%)`;
      // 把原裁剪图画上去
      tempCtx.drawImage(canvas, 0, 0);
      // 把处理好的图写回原 Canvas (或者直接用 tempCanvas 导出)
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(tempCanvas, 0, 0);
    }
  }

  // 3. 导出为 Blob 文件并上传
  canvas.toBlob(
    async blob => {
      if (!blob) {
        saving.value = false;
        return;
      }

      const formData = new FormData();
      // 生成一个文件名
      const filename = `edited_${Date.now()}.jpg`;
      formData.append("file", blob, filename);

      try {
        const res = await axios.post("/api/image/upload", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: "Bearer " + getToken()?.accessToken
          }
        });

        if (res.data.code === 200) {
          message("编辑并保存成功！", { type: "success" });
          dialogVisible.value = false;
          // 刷新列表
          if (props.refreshList) props.refreshList();
        } else {
          message("保存失败: " + res.data.msg, { type: "error" });
        }
      } catch (error) {
        message("网络错误", { type: "error" });
      } finally {
        saving.value = false;
      }
    },
    "image/jpeg",
    0.9
  ); // 0.9 是质量
};

// 暴露 open 方法
defineExpose({ open });
</script>

<style>
/* 强制覆盖 cropper 的一些样式，防止被 tailwind 影响 */
.cropper-container img {
  display: block;
  max-width: 100%;
}
</style>
