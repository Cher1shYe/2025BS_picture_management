<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { message } from "@/utils/message";
import { getToken } from "@/utils/auth";
import { getUserInfo, updateUserInfo, updateUserPassword } from "@/api/user";
import { useUserStoreHook } from "@/store/modules/user";
import { Plus } from "@element-plus/icons-vue";
import axios from "axios"; // 引入 axios 处理文件上传更直观

defineOptions({ name: "Person" });

const userStore = useUserStoreHook();
const activeTab = ref("info");
const loading = ref(false);

// 用户基本信息表单
const infoForm = reactive({
  username: "",
  email: "",
  avatar: ""
});

// 密码表单
const pwdForm = reactive({
  oldPassword: "",
  newPassword: ""
});

// 获取最新数据
const fetchData = async () => {
  const { data } = await getUserInfo();
  infoForm.username = data.username;
  infoForm.email = data.email || "";
  infoForm.avatar = data.avatar || "";
  // 同步更新 Store 里的头像，保证右上角也变
  userStore.SET_AVATAR(data.avatar);
  userStore.SET_USERNAME(data.username);
};

// 更新基本信息
const handleUpdateInfo = async () => {
  loading.value = true;
  try {
    await updateUserInfo({
      username: infoForm.username,
      email: infoForm.email
    });
    message("保存成功", { type: "success" });
    fetchData(); // 刷新
  } finally {
    loading.value = false;
  }
};

// 修改密码
const handleUpdatePwd = async () => {
  // 1. 简单校验
  if (!pwdForm.oldPassword || !pwdForm.newPassword) {
    return message("请填写完整旧密码和新密码", { type: "warning" });
  }
  if (pwdForm.newPassword.length < 6) {
    return message("新密码长度不能少于6位", { type: "warning" });
  }

  try {
    // 2. 发送请求
    const res: any = await updateUserPassword({
      oldPassword: pwdForm.oldPassword,
      newPassword: pwdForm.newPassword
    });

    console.log("修改密码响应:", res); // [调试] F12看这里

    // 3. 判断结果
    if (res.success || res.code === 200) {
      message("密码修改成功，请重新登录", { type: "success" });
      userStore.logOut();
    } else {
      // 显示后端返回的 msg
      message(res.msg || "修改失败", { type: "error" });
    }
  } catch(err: any) {
    // 4. 捕获深层错误 (400/500)
    console.error("修改密码报错:", err);
    // 尝试读取后端返回的具体错误信息
    const errorMsg = err.response?.data?.msg || "请求出错，请检查网络";
    message(errorMsg, { type: "error" });
  }
};

// 自定义上传头像
const customUpload = async (options: any) => {
  const formData = new FormData();
  formData.append("file", options.file);

  try {
    // 这里直接用 axios 发请求，避开封装的复杂性
    const res = await axios.post("/api/user/update/avatar", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: "Bearer " + getToken()?.accessToken
      }
    });
    if (res.data.code === 200) {
      message("头像上传成功", { type: "success" });
      infoForm.avatar = res.data.data.avatar;
      userStore.SET_AVATAR(res.data.data.avatar); // 更新全局状态
    } else {
      message(res.data.msg, { type: "error" });
    }
  } catch (error) {
    message("上传出错", { type: "error" });
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <el-card shadow="never">
    <el-tabs v-model="activeTab">
      <!-- 个人资料 -->
      <el-tab-pane label="个人资料" name="info">
        <div class="flex">
          <!-- 左侧头像 -->
          <div class="w-1/3 flex flex-col items-center pt-5">
            <el-upload
              class="avatar-uploader"
              action="#"
              :show-file-list="false"
              :http-request="customUpload"
            >
              <img
                v-if="infoForm.avatar"
                :src="infoForm.avatar"
                class="avatar"
              />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <span class="text-gray-400 text-sm mt-2">点击图片更换头像</span>
          </div>

          <!-- 右侧表单 -->
          <div class="w-1/2">
            <el-form label-position="top">
              <el-form-item label="用户名">
                <el-input v-model="infoForm.username" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="infoForm.email" />
              </el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleUpdateInfo"
                >保存修改</el-button
              >
            </el-form>
          </div>
        </div>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="安全设置" name="security">
        <div class="w-1/2 p-5">
          <el-form label-position="top">
            <el-form-item label="旧密码">
              <el-input
                v-model="pwdForm.oldPassword"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="pwdForm.newPassword"
                type="password"
                show-password
              />
            </el-form-item>
            <el-button type="danger" @click="handleUpdatePwd"
              >确认修改密码</el-button
            >
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.avatar-uploader .avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: block;
  object-fit: cover;
  border: 1px solid #eee;
}
.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  border: 1px dashed #d9d9d9;
  text-align: center;
  line-height: 150px;
  cursor: pointer;
}
.avatar-uploader-icon:hover {
  border-color: #409eff;
}
</style>
