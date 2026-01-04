<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted } from "vue";
import { message } from "@/utils/message";
import { getToken } from "@/utils/auth";
import axios from "axios";
// 引入图标：增加 MagicStick (用于AI)
import {
  Plus,
  Search,
  Refresh,
  Delete,
  Location,
  Edit,
  MagicStick
} from "@element-plus/icons-vue";
import { ElMessageBox } from "element-plus";
import ImageEditor from "@/components/ImageEditor/index.vue";

defineOptions({
  name: "ImageList"
});

// --- 1. 响应式状态 ---
const isMobile = ref(false); // 是否移动端
const loading = ref(false);
const imageList = ref([]);
const total = ref(0);
const allTags = ref([]); // 标签下拉数据源
const editorRef = ref(); // 编辑器引用

const queryParams = reactive({
  page: 1,
  limit: 12,
  keyword: "",
  location: "",
  tag_id: null,
  dateRange: [] as string[] // 时间范围
});

// --- 2. 移动端检测逻辑 ---
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768;
};

// --- 3. API 请求封装 ---
// 通用请求头生成器
const getHeaders = (isForm = false) => ({
  headers: {
    Authorization: "Bearer " + getToken()?.accessToken,
    "Content-Type": isForm ? "multipart/form-data" : "application/json"
  }
});

// 获取所有标签
const getAllTags = async () => {
  try {
    const res = await axios.get("/api/image/all_tags", getHeaders());
    if (res.data.code === 200) allTags.value = res.data.data;
  } catch (e) {
    console.error(e);
  }
};

// 获取图片列表 (核心查询)
const getImages = async () => {
  loading.value = true;
  try {
    // 处理时间参数：兼容手机端拆分的日期 和 PC端的日期范围数组
    let start_date = "";
    let end_date = "";
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      start_date = queryParams.dateRange[0] || "";
      end_date = queryParams.dateRange[1] || "";
    }

    const res = await axios.get("/api/image/list", {
      params: {
        page: queryParams.page,
        limit: queryParams.limit,
        keyword: queryParams.keyword,
        location: queryParams.location,
        tag_id: queryParams.tag_id,
        start_date: start_date,
        end_date: end_date
      },
      ...getHeaders()
    });

    if (res.data.code === 200) {
      imageList.value = res.data.data.items;
      total.value = res.data.data.total;
    }
  } catch (error) {
    message("加载列表失败", { type: "error" });
  } finally {
    loading.value = false;
  }
};

// --- 4. 交互操作逻辑 ---

// 搜索与重置
const handleSearch = () => {
  queryParams.page = 1;
  getImages();
};
const handleReset = () => {
  queryParams.keyword = "";
  queryParams.location = "";
  queryParams.tag_id = null;
  queryParams.dateRange = [];
  handleSearch();
};

// 上传图片
const handleUpload = async (options: any) => {
  const formData = new FormData();
  formData.append("file", options.file);
  try {
    const res = await axios.post(
      "/api/image/upload",
      formData,
      getHeaders(true)
    );
    if (res.data.code === 200) {
      message("上传成功", { type: "success" });
      handleSearch();
    } else {
      message(res.data.msg || "上传失败", { type: "error" });
    }
  } catch (e) {
    message("上传出错", { type: "error" });
  }
};

// 删除图片
const handleDelete = (id: number) => {
  ElMessageBox.confirm("确定要永久删除这张图片吗？", "警告", {
    confirmButtonText: "删除",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    try {
      const res = await axios.post("/api/image/delete", { id }, getHeaders());
      if (res.data.code === 200) {
        message("删除成功", { type: "success" });
        getImages();
        getAllTags();
      }
    } catch (e) {
      message("删除请求失败", { type: "error" });
    }
  });
};

// 手动添加标签
const handleAddTag = (imageId: number) => {
  ElMessageBox.prompt("请输入新标签名称", "添加标签", {
    inputPattern: /\S+/,
    inputErrorMessage: "标签不能为空"
  }).then(async ({ value }) => {
    const res = await axios.post(
      "/api/image/add_tag",
      { image_id: imageId, tag_name: value },
      getHeaders()
    );
    if (res.data.code === 200) {
      message("添加成功", { type: "success" });
      getImages();
      getAllTags();
    }
  });
};

// 移除标签
const handleRemoveTag = async (imageId: number, tagName: string) => {
  try {
    const res = await axios.post(
      "/api/image/remove_tag",
      { image_id: imageId, tag_name: tagName },
      getHeaders()
    );
    if (res.data.code === 200) {
      message("标签已移除", { type: "success" });
      getImages();
      getAllTags();
    }
  } catch (e) {
    message("移除失败", { type: "error" });
  }
};

// 打开编辑器
const handleEdit = (item: any) => {
  editorRef.value.open(item.url);
};
const onEditorSuccess = () => {
  getImages();
};

// AI 分析 (核心功能)
const handleAnalyze = async (item: any) => {
  item.isAnalyzing = true;
  try {
    const res = await axios.post(
      `/api/ai/analyze/${item.id}`,
      {},
      getHeaders()
    );
    if (res.data.code === 200) {
      const tags = res.data.data;
      message(
        tags.length > 0 ? `识别成功: ${tags.join(", ")}` : "未识别出新标签",
        { type: "success" }
      );
      getImages();
      getAllTags(); // 刷新搜索栏
    } else {
      message(res.data.msg, { type: "warning" });
    }
  } catch (e) {
    message("AI 服务暂时不可用", { type: "error" });
  } finally {
    item.isAnalyzing = false;
  }
};

// 分页处理
const handleSizeChange = (val: number) => {
  queryParams.limit = val;
  getImages();
};
const handleCurrentChange = (val: number) => {
  queryParams.page = val;
  getImages();
};

// --- 5. 生命周期 ---
onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
  getAllTags();
  getImages();
});
onUnmounted(() => {
  window.removeEventListener("resize", checkMobile);
});
</script>

<template>
  <div class="image-page">
    <!-- 1. 顶部筛选栏 (响应式布局) -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-flex">
        <div class="input-grid">
          <!-- 关键词 -->
          <el-input
            v-model="queryParams.keyword"
            placeholder="文件名"
            clearable
            class="grid-item"
            @keyup.enter="handleSearch"
          />
          <!-- 地点 -->
          <el-input
            v-model="queryParams.location"
            placeholder="地点 (GPS)"
            clearable
            :prefix-icon="Location"
            class="grid-item"
            @keyup.enter="handleSearch"
          />
          <!-- 标签 -->
          <el-select
            v-model="queryParams.tag_id"
            placeholder="标签筛选"
            clearable
            filterable
            class="grid-item"
            @change="handleSearch"
          >
            <el-option
              v-for="tag in allTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>

          <!-- 日期选择：PC端显示范围选择，手机端显示两个独立框 -->
          <div v-if="!isMobile" class="grid-item date-range-wrapper">
            <el-date-picker
              v-model="queryParams.dateRange"
              type="daterange"
              range-separator="-"
              start-placeholder="开始"
              end-placeholder="结束"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              @change="handleSearch"
            />
          </div>
          <template v-else>
            <!-- 手机端拆分日期，防止挤压 -->
            <el-date-picker
              v-model="queryParams.dateRange[0]"
              type="date"
              placeholder="开始日期"
              value-format="YYYY-MM-DD"
              class="grid-item"
              @change="handleSearch"
            />
            <el-date-picker
              v-model="queryParams.dateRange[1]"
              type="date"
              placeholder="结束日期"
              value-format="YYYY-MM-DD"
              class="grid-item"
              @change="handleSearch"
            />
          </template>
        </div>

        <!-- 按钮组 -->
        <div class="btn-group">
          <el-button type="primary" :icon="Search" @click="handleSearch"
            >搜索</el-button
          >
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-upload
            action="#"
            :auto-upload="true"
            :show-file-list="false"
            :http-request="handleUpload"
            accept="image/*"
          >
            <el-button type="success" :icon="Plus">上传</el-button>
          </el-upload>
        </div>
      </div>
    </el-card>

    <!-- 2. 图片列表 (响应式 Grid) -->
    <el-card v-loading="loading" shadow="never" class="list-card mt-4">
      <el-empty v-if="imageList.length === 0" description="暂无图片" />
      <!-- :xs="12" 保证手机一行两个，更加美观 -->
      <el-row :gutter="isMobile ? 10 : 20">
        <el-col
          v-for="(item, index) in imageList"
          :key="item.id"
          :xs="12"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
          class="mb-4"
        >
          <el-card
            :body-style="{ padding: '0px' }"
            shadow="hover"
            class="img-item-card group"
          >
            <!-- 图片主体 -->
            <el-image
              class="img-display"
              :src="item.thumb || item.url"
              fit="cover"
              :preview-src-list="imageList.map(v => v.url)"
              :initial-index="index"
              lazy
            />
            <div class="p-2 sm:p-3">
              <!-- 标题 -->
              <div class="img-title">{{ item.name }}</div>
              <!-- 信息行：日期 + 地点 -->
              <div class="img-info">
                <span>{{ item.date }}</span>
                <span v-if="item.location" class="loc-text">
                  📍{{ item.location }}</span
                >
              </div>
              <!-- 标签行 -->
              <div class="tags-wrapper">
                <el-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  size="small"
                  closable
                  class="mr-1 mb-1"
                  @close="handleRemoveTag(item.id, tag)"
                >
                  {{ tag }}
                </el-tag>
                <el-button
                  size="small"
                  circle
                  :icon="Plus"
                  class="add-tag-btn"
                  @click="handleAddTag(item.id)"
                />
              </div>

              <!-- 底部操作栏 -->
              <div class="card-footer">
                <!-- 删除按钮 -->
                <el-button
                  type="danger"
                  link
                  size="small"
                  :icon="Delete"
                  @click="handleDelete(item.id)"
                >
                  <span v-if="!isMobile">删除</span>
                </el-button>
                <!-- 右侧操作组 -->
                <div class="flex gap-1">
                  <!-- 编辑 -->
                  <el-button
                    type="primary"
                    circle
                    size="small"
                    :icon="Edit"
                    @click.stop="handleEdit(item)"
                  />
                  <!-- AI 识别 -->
                  <el-button
                    type="warning"
                    circle
                    size="small"
                    :icon="MagicStick"
                    :loading="item.isAnalyzing"
                    @click="handleAnalyze(item)"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 3. 分页 -->
      <div class="pagination-box">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :page-sizes="[12, 24, 48]"
          :small="isMobile"
          :layout="
            isMobile
              ? 'prev, pager, next'
              : 'total, sizes, prev, pager, next, jumper'
          "
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 图片编辑器组件 -->
    <ImageEditor ref="editorRef" :refresh-list="onEditorSuccess" />
  </div>
</template>

<style scoped>
.image-page {
  padding: 16px;
}

/* --- 筛选区 --- */
.filter-flex {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.input-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.grid-item {
  width: 140px;
  flex-grow: 1;
}
.date-range-wrapper {
  width: 280px;
  flex-grow: 2;
}
.btn-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* --- 图片卡片 --- */
.img-item-card {
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s;
}
.img-item-card:hover {
  transform: translateY(-4px);
}

.img-display {
  width: 100%;
  height: 180px;
  display: block;
}

.img-title {
  font-size: 14px;
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.img-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
  margin: 4px 0;
}
.loc-text {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 标签区高度限制，防止卡片过长 */
.tags-wrapper {
  min-height: 28px;
  max-height: 56px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
/* 隐藏标签区的滚动条 */
.tags-wrapper::-webkit-scrollbar {
  display: none;
}

.add-tag-btn {
  transform: scale(0.8);
  margin-bottom: 4px;
}

/* 底部操作栏 */
.card-footer {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-box {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* --- 移动端适配 (重点) --- */
@media (max-width: 768px) {
  .image-page {
    padding: 8px;
  }

  /* 强制两列布局时的间距微调 */
  .grid-item {
    width: calc(50% - 4px) !important;
    min-width: 0 !important;
  }

  /* 图片变矮，适应小屏 */
  .img-display {
    height: 120px;
  }

  /* 按钮均分宽度 */
  .btn-group {
    justify-content: space-between;
  }
  .btn-group .el-button {
    flex: 1;

    .pagination-box {
      justify-content: center;
    }

    /* 手机端隐藏文字只显示图标 */
    .loc-text {
      max-width: 60px;
    }
  }
}
</style>
