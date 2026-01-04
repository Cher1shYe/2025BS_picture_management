<script setup lang="ts">
import { ref, nextTick, reactive } from "vue";
import axios from "axios";
import { getToken } from "@/utils/auth";
import {
  ChatDotRound,
  Position,
  Close,
  Picture as IconPicture
} from "@element-plus/icons-vue";

const API_BASE_URL = "http://localhost:5001";

// --- 新增一个处理图片路径的函数 ---
const getFullImageUrl = (url: string) => {
  if (!url) return "";
  // 如果已经是完整链接 (http开头)，直接返回
  if (url.startsWith("http") || url.startsWith("https")) {
    return url;
  }
  // 如果是相对路径，拼接后端地址
  return `${API_BASE_URL}${url}`;
};

// --- 状态 ---
const isOpen = ref(false);
const inputVal = ref("");
const loading = ref(false);
const messages = ref<any[]>([
  {
    role: "assistant",
    content:
      '你好！我是基于 MCP 协议的 AI 助手。你可以对我说："找一下去年在杭州拍的猫的照片"。'
  }
]);
const scrollInner = ref();

// --- 方法 ---

// 发送消息
const sendMessage = async () => {
  if (!inputVal.value.trim() || loading.value) return;

  const text = inputVal.value;
  // 1. 添加用户消息
  messages.value.push({ role: "user", content: text });
  inputVal.value = "";
  loading.value = true;
  scrollToBottom();

  try {
    // 2. 准备历史记录 (OpenAI 格式: user/assistant)
    const history = messages.value.slice(-6).map(m => ({
      role: m.role,
      content: m.content
    }));

    // 3. 请求后端
    const res = await axios.post(
      "/api/chat/ask",
      {
        message: text,
        history
      },
      {
        headers: { Authorization: "Bearer " + getToken()?.accessToken }
      }
    );

    if (res.data.code === 200) {
      const data = res.data.data;
      // 添加 AI 回复
      messages.value.push({
        role: "assistant",
        content: data.text,
        images: data.images || [] // 如果有图片
      });
    } else {
      messages.value.push({
        role: "assistant",
        content: "出错了: " + res.data.msg
      });
    }
  } catch (e) {
    messages.value.push({ role: "assistant", content: "网络连接失败" });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollInner.value) {
      scrollInner.value.scrollTop = scrollInner.value.scrollHeight;
    }
  });
};

const openImage = (url: string) => {
  window.open(getFullImageUrl(url), "_blank");
};
</script>

<template>
  <div>
    <!-- 1. 悬浮球 (右下角) -->
    <div class="float-btn" @click="isOpen = true" v-if="!isOpen">
      <el-icon :size="28" color="#fff"><ChatDotRound /></el-icon>
    </div>

    <!-- 2. 全屏/半屏弹窗 -->
    <div v-if="isOpen" class="chat-overlay" @click.self="isOpen = false">
      <div class="chat-window">
        <!-- 顶部 -->
        <div class="chat-header">
          <span class="title">DeepSeek 图片搜素</span>
          <el-icon class="close-btn" @click="isOpen = false"><Close /></el-icon>
        </div>

        <!-- 消息区 -->
        <div class="chat-body" ref="scrollInner">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            :class="['msg-row', msg.role === 'user' ? 'msg-right' : 'msg-left']"
          >
            <!-- 头像 (可选) -->
            <div class="avatar" v-if="msg.role === 'assistant'">🤖</div>

            <div class="msg-content-wrapper">
              <!-- 文本气泡 -->
              <div class="bubble">
                {{ msg.content }}
              </div>

              <!-- 图片结果 (横向滚动) -->
              <div v-if="msg.images && msg.images.length" class="img-scroller">
                <div
                  v-for="img in msg.images"
                  :key="img.id"
                  class="img-card"
                  @click="openImage(img.url)"
                >
                  <img :src="getFullImageUrl(img.thumb)" loading="lazy" />
                  <div class="img-meta">
                    <div class="t1">{{ img.name }}</div>
                    <div class="t2">{{ img.date.split(" ")[0] }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="loading" class="msg-row msg-left">
            <div class="avatar">🤖</div>
            <div class="bubble loading">思考中...</div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-footer">
          <el-input
            v-model="inputVal"
            placeholder="说点什么..."
            class="chat-input"
            @keyup.enter="sendMessage"
          >
            <template #append>
              <el-button
                :icon="Position"
                :loading="loading"
                @click="sendMessage"
              />
            </template>
          </el-input>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 悬浮按钮 */
.float-btn {
  position: fixed;
  right: 20px;
  bottom: 80px;
  width: 56px;
  height: 56px;
  background: #409eff;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2000;
  transition: transform 0.2s;
}
.float-btn:active {
  transform: scale(0.9);
}

/* 聊天窗口容器 */
.chat-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2001;
  display: flex;
  justify-content: center;
  align-items: flex-end; /* 手机端从底部弹出 */
}

/* 响应式窗口 */
.chat-window {
  width: 100%;
  height: 80vh; /* 手机端高度 */
  background: #fff;
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease-out;
}
@media (min-width: 768px) {
  /* PC端样式 */
  .chat-overlay {
    align-items: center;
  }
  .chat-window {
    width: 400px;
    height: 600px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.close-btn {
  cursor: pointer;
  font-size: 20px;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
}

/* 消息行 */
.msg-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.msg-left {
  flex-direction: row;
}
.msg-right {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  background: #ddd;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.msg-content-wrapper {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}
.msg-left .bubble {
  background: #fff;
  border-bottom-left-radius: 2px;
}
.msg-right .bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 2px;
}

/* 图片滚动条 */
.img-scroller {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}
/* 隐藏滚动条但保留功能 */
.img-scroller::-webkit-scrollbar {
  height: 4px;
}
.img-scroller::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 2px;
}

.img-card {
  flex-shrink: 0;
  width: 120px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}
.img-card img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}
.img-meta {
  padding: 4px 6px;
  font-size: 10px;
}
.t1 {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.t2 {
  color: #999;
}

.chat-footer {
  padding: 10px;
  border-top: 1px solid #eee;
  background: #fff;
}
</style>
