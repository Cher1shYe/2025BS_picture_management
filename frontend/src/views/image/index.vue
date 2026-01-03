<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { message } from "@/utils/message";
import { getToken } from "@/utils/auth";
import axios from "axios";
import {
  Plus,
  Search,
  Refresh,
  Delete,
  PriceTag,
  Location,
  Edit
} from "@element-plus/icons-vue";
// 引入 Delete 图标 和 ElMessageBox 弹窗组件
import { ElMessageBox } from "element-plus";

import ImageEditor from "@/components/ImageEditor/index.vue";

defineOptions({
  name: "ImageList"
});

const loading = ref(false);
const imageList = ref([]);
const total = ref(0);
const allTags = ref([]); // 存储供筛选的标签列表

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 12,
  keyword: "",
  location: "", // 【新增】地点
  tag_id: null, // 【新增】标签ID筛选
  dateRange: [] // 【新增】时间范围数组 [start, end]
});

/** 【新增】 获取系统所有标签 (用于下拉框) */
const getAllTags = async () => {
  try {
    const res = await axios.get("/api/image/all_tags", {
      headers: { Authorization: "Bearer " + getToken()?.accessToken }
    });
    if (res.data.code === 200) {
      allTags.value = res.data.data;
    }
  } catch (e) {
    console.error(e);
  }
};

/** 1. 获取图片列表 */
const getImages = async () => {
  loading.value = true;
  try {
    // 处理时间参数
    let start_date = "";
    let end_date = "";
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      start_date = queryParams.dateRange[0];
      end_date = queryParams.dateRange[1];
    }
    const res = await axios.get("/api/image/list", {
      params: {
        page: queryParams.page,
        limit: queryParams.limit,
        keyword: queryParams.keyword,
        location: queryParams.location, // 传给后端
        tag_id: queryParams.tag_id,
        start_date: start_date,
        end_date: end_date
      },
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
/** 【新增】重制搜索处理 */
const handleReset = () => {
  queryParams.keyword = "";
  queryParams.location = "";
  queryParams.tag_id = null;
  queryParams.dateRange = [];
  handleSearch();
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

/** 【新增】处理删除逻辑 */
const handleDelete = (id: number) => {
  ElMessageBox.confirm("确定要永久删除这张图片吗？此操作不可恢复", "警告", {
    confirmButtonText: "确定删除",
    cancelButtonText: "取消",
    type: "warning"
  })
    .then(async () => {
      try {
        const res = await axios.post(
          "/api/image/delete",
          { id: id },
          {
            headers: { Authorization: "Bearer " + getToken()?.accessToken }
          }
        );

        if (res.data.code === 200) {
          message("删除成功", { type: "success" });
          // 刷新列表
          getImages();
          getAllTags();
        } else {
          message(res.data.msg || "删除失败", { type: "error" });
        }
      } catch (error) {
        message("请求出错", { type: "error" });
      }
    })
    .catch(() => {
      // 用户点击取消，不做任何事
    });
};

/** 【新增】给图片手动添加标签 */
const handleAddTag = (imageId: number) => {
  ElMessageBox.prompt("请输入新标签名称 (例如: 家人, 旅行)", "添加标签", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPattern: /\S+/,
    inputErrorMessage: "标签名不能为空"
  }).then(async ({ value }) => {
    try {
      const res = await axios.post(
        "/api/image/add_tag",
        { image_id: imageId, tag_name: value },
        { headers: { Authorization: "Bearer " + getToken()?.accessToken } }
      );
      if (res.data.code === 200) {
        message("标签添加成功", { type: "success" });
        getImages(); // 刷新列表显示新标签
        getAllTags(); // 刷新下拉框
      }
    } catch (e) {
      message("添加失败", { type: "error" });
    }
  });
};

/** 【新增】移除标签 */
const handleRemoveTag = async (imageId: number, tagName: string) => {
  try {
    const res = await axios.post(
      "/api/image/remove_tag",
      { image_id: imageId, tag_name: tagName },
      { headers: { Authorization: "Bearer " + getToken()?.accessToken } }
    );
    if (res.data.code === 200) {
      message("已移除标签", { type: "success" });
      // 可以在这里手动从 imageList 里移除该标签以避免重新加载整个列表，
      // 但为了数据一致性，重新获取列表最简单
      getImages();
      getAllTags(); // 刷新下拉筛选框，让已经删除的标签不在搜索选项中出现
    } else {
      message(res.data.msg, { type: "warning" });
    }
  } catch (e) {
    message("移除失败", { type: "error" });
  }
};

/** 处理分页切换 */
const handleSizeChange = (val: number) => {
  queryParams.limit = val;
  getImages();
};

const handleCurrentChange = (val: number) => {
  queryParams.page = val;
  getImages();
};

const editorRef = ref();

// 点击编辑按钮触发的函数
const handleEdit = (item: any) => {
  // 传入原图 URL（注意不是缩略图）
  editorRef.value.open(item.url);
};

// 编辑保存后的回调（刷新列表）
const onEditorSuccess = () => {
  getImages();
};

onMounted(() => {
  getAllTags();
  getImages();
});
</script>

<template>
  <div class="main">
    <el-card shadow="never" class="mb-4">
      <div class="flex flex-wrap gap-4 justify-between items-center">
        <!-- 左侧：组合搜索区 -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- 文件名搜索 -->
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索文件名..."
            style="width: 200px"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <!-- 2. 【新增】地点搜索 -->
          <el-input
            v-model="queryParams.location"
            placeholder="搜索拍摄地点 (GPS)"
            style="width: 180px"
            clearable
            :prefix-icon="Location"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <!-- 标签筛选 -->
          <el-select
            v-model="queryParams.tag_id"
            placeholder="按标签筛选"
            clearable
            filterable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option
              v-for="tag in allTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
          <!-- 3. 时间范围 -->
          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            @change="handleSearch"
          />
          <el-button type="primary" :icon="Search" @click="handleSearch"
            >搜索</el-button
          >
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </div>
        <!-- 右侧：上传按钮 -->
        <el-upload
          action="#"
          :auto-upload="true"
          :show-file-list="false"
          :http-request="handleUpload"
          accept="image/*"
        >
          <el-button type="success" :icon="Plus">上传图片</el-button>
        </el-upload>
      </div>
    </el-card>

    <!-- 图片列表 -->
    <el-card shadow="never" v-loading="loading" class="min-h-[500px]">
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
            class="image-card group"
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
              <!-- 名称 -->
              <div class="text-sm font-bold truncate">{{ item.name }}</div>
              <!-- 信息行 -->
              <div
                class="flex justify-between items-center text-xs text-gray-400 mb-2"
              >
                <span>{{ item.date }}</span>
                <span
                  v-if="item.location"
                  class="truncate max-w-[80px]"
                  :title="item.location"
                >
                  📍 {{ item.location }}
                </span>
              </div>
              <!-- 标签区 (带添加按钮) -->
              <div class="flex flex-wrap gap-1 mb-3 min-h-[24px]">
                <el-tag
                  v-for="tag in item.tags"
                  :key="tag"
                  size="small"
                  effect="light"
                  closable
                  @close="handleRemoveTag(item.id, tag)"
                >
                  {{ tag }}
                </el-tag>
                <!-- 添加标签的小按钮 -->
                <el-button
                  size="small"
                  circle
                  :icon="Plus"
                  class="scale-75"
                  title="添加标签"
                  @click="handleAddTag(item.id)"
                />
              </div>
              <!-- 【修改 2】新增：底部操作栏 (分割线 + 删除按钮) -->
              <div
                class="mt-3 pt-2 border-t border-gray-100 flex justify-between items-center"
              >
                <!-- 底部操作：删除按钮，红色，文字按钮，带图标 -->
                <el-button
                  type="danger"
                  link
                  size="small"
                  :icon="Delete"
                  @click="handleDelete(item.id)"
                >
                  删除
                </el-button>
                <!-- 【新增】编辑按钮 -->
                <el-button
                  type="primary"
                  circle
                  size="small"
                  :icon="Edit"
                  title="编辑图片"
                  @click.stop="handleEdit(item)"
                />
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
    <ImageEditor ref="editorRef" :refresh-list="onEditorSuccess" />
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
