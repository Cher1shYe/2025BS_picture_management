<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { message } from "@/utils/message";
import { getToken } from "@/utils/auth";
import axios from "axios";
import { Plus, Search, Refresh } from "@element-plus/icons-vue";

defineOptions({
  name: "ImageList"
});

const loading = ref(false);
const imageList = ref([]);
const total = ref(0);

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 12,
  keyword: ""
});

/** 1. 获取图片列表 */
const getImages = async () => {
  loading.value = true;
  try {
    const res = await axios.get("/api/image/list", {
      params: queryParams,
      headers: { Authorization: "Bearer " + getToken()?.accessToken }
    });

    if (res.data.code === 200) {
      // 对接后端返回的 items 数组
      imageList.value = res.data.data.items;
      total.value = res.data.data.total;
    }
  } catch (error) {
    message("加载列表失败", { type: "error" });
  } finally {
    loading.value = false;
  }
};

/** 2. 处理搜索 */
const handleSearch = () => {
  queryParams.page = 1; // 搜索时重置回第一页
  getImages();
};

/** 3. 处理上传 */
const handleUpload = async (options: any) => {
  const formData = new FormData();
  formData.append("file", options.file);

  try {
    const res = await axios.post("/api/image/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: "Bearer " + getToken()?.accessToken
      }
    });

    if (res.data.code === 200) {
      message("图片上传成功", { type: "success" });
      handleSearch(); // 上传后刷新并回到第一页
    } else {
      message(res.data.msg || "上传失败", { type: "error" });
    }
  } catch (error) {
    message("网络请求出错", { type: "error" });
  }
};

/** 4. 处理分页切换 */
const handleSizeChange = (val: number) => {
  queryParams.limit = val;
  getImages();
};

const handleCurrentChange = (val: number) => {
  queryParams.page = val;
  getImages();
};

onMounted(() => {
  getImages();
});
</script>

<template>
  <div class="main">
    <el-card shadow="never" class="mb-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center">
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索图片名称或地点..."
            style="width: 260px"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
          <el-button :icon="Refresh" class="ml-2" @click="handleSearch" />
        </div>

        <el-upload
          action="#"
          :auto-upload="true"
          :show-file-list="false"
          :http-request="handleUpload"
          accept="image/*"
        >
          <el-button type="primary" :icon="Plus">上传新图片</el-button>
        </el-upload>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="imageList.length === 0" description="没有找到相关图片" />

      <el-row :gutter="20">
        <el-col
          v-for="(item, index) in imageList"
          :key="item.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
          class="mb-6"
        >
          <el-card
            :body-style="{ padding: '0px' }"
            shadow="hover"
            class="image-card"
          >
            <el-image
              style="width: 100%; height: 200px"
              :src="item.thumb || item.url"
              fit="cover"
              :preview-src-list="imageList.map(v => v.url)"
              :initial-index="index"
              lazy
            />
            <div class="p-3">
              <div class="text-sm font-bold truncate">{{ item.name }}</div>
              <div class="flex justify-between items-center mt-2">
                <span class="text-xs text-gray-400">{{ item.date }}</span>
                <el-tag v-if="item.location" size="small" effect="plain">
                  {{ item.location }}
                </el-tag>
              </div>
              <div class="mt-2 flex flex-wrap gap-1">
                <el-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :page-sizes="[12, 24, 48, 96]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.main {
  margin: 24px;
}
.image-card {
  transition: transform 0.3s;
  border-radius: 8px;
  overflow: hidden;
}
.image-card:hover {
  transform: translateY(-5px);
}
</style>
