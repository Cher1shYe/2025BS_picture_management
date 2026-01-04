<script setup lang="ts">
import Motion from "./utils/motion";
import { useRouter } from "vue-router";
import { message } from "@/utils/message";
import { loginRules } from "./utils/rule";
import { ref, reactive, toRaw } from "vue";
import { debounce } from "@pureadmin/utils";
import { useNav } from "@/layout/hooks/useNav";
import { useEventListener } from "@vueuse/core";
import type { FormInstance } from "element-plus";
import { useLayout } from "@/layout/hooks/useLayout";
import { useUserStoreHook } from "@/store/modules/user";
import { initRouter, getTopMenu } from "@/router/utils";
import { bg, avatar, illustration } from "./utils/static";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { useDataThemeChange } from "@/layout/hooks/useDataThemeChange";
import { getRegister } from "@/api/user";

import MyLogo from "@/assets/logo.jpg";
import dayIcon from "@/assets/svg/day.svg?component";
import darkIcon from "@/assets/svg/dark.svg?component";
import Lock from "~icons/ri/lock-fill";
import User from "~icons/ri/user-3-fill";
// 新增：邮箱图标
import Mail from "~icons/ri/mail-fill";

defineOptions({
  name: "Login"
});

const router = useRouter();
const loading = ref(false);
// [新增] 控制当前是登录还是注册状态 (false: 登录, true: 注册)
const isRegister = ref(false);
const disabled = ref(false);
const ruleFormRef = ref<FormInstance>();

const { initStorage } = useLayout();
initStorage();

const { dataTheme, overallStyle, dataThemeChange } = useDataThemeChange();
dataThemeChange(overallStyle.value);
const { title } = useNav();

const ruleForm = reactive({
  username: "",
  password: "",
  email: "" // [新增] 邮箱字段
});

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  // 清空表单，避免串台
  ruleForm.username = "";
  ruleForm.password = "";
  ruleForm.email = "";
};

const onSubmit = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate(valid => {
    if (valid) {
      loading.value = true;
      if (isRegister.value) {
        // --- 注册逻辑 ---
        getRegister({
          username: ruleForm.username,
          password: ruleForm.password,
          email: ruleForm.email
        })
          .then((res: any) => {
            // 注意：axios拦截器可能会处理res结构，根据实际情况调整
            if (res.code === 200) {
              message("注册成功，请登录", { type: "success" });
              toggleMode(); // 注册成功后自动切回登录
            } else {
              // 显式弹出错误信息，防止“闪一下没反应”
              message(res.msg || "注册失败，请检查输入", { type: "error" });
            }
          })
          .catch(err => {
            // [优化] 显示后端返回的具体错误
            const errorMsg = err.response?.data?.msg || "注册请求出错";
            message(errorMsg, { type: "error" });
          })
          .finally(() => (loading.value = false));
      } else {
        useUserStoreHook()
          .loginByUsername({
            username: ruleForm.username,
            password: ruleForm.password
          })
          .then(res => {
            console.log("登录接口返回:", res); // [调试] 关键点！看这里打印了什么
            if (res.success || res.code === 200) {
              // 获取后端路由
              initRouter().then(() => {
                router.push(getTopMenu(true).path);
                message("登录成功", { type: "success" });
              });
            } else {
              message(res.msg || "登录失败", { type: "error" });
            }
          })
          .catch(err => {
            // [优化] 捕获 401/400 等错误，显示具体原因（如：密码错误）
            console.error("登录报错详情:", err);
            const errorMsg =
              err.response?.data?.msg || "登录请求失败，请检查网络或账号密码";
            message("登录请求失败", { type: "error" });
          })
          .finally(() => (loading.value = false));
      }
    }
  });
};

const immediateDebounce: any = debounce(
  formRef => onSubmit(formRef),
  1000,
  true
);
</script>

<template>
  <div class="select-none">
    <img :src="bg" class="wave" />
    <div class="flex-c absolute right-5 top-3">
      <el-switch
        v-model="dataTheme"
        inline-prompt
        :active-icon="dayIcon"
        :inactive-icon="darkIcon"
        @change="dataThemeChange"
      />
    </div>
    <div class="login-container">
      <div class="img">
        <component :is="toRaw(illustration)" />
      </div>
      <div class="login-box">
        <div class="login-form">
          <div class="logo-wrapper">
            <img :src="MyLogo" class="custom-logo" alt="logo" />
          </div>
          <Motion>
            <h2 class="outline-hidden">
              Picture Manager <br />
              {{ isRegister ? "账号注册" : "账号登录" }}
            </h2>
          </Motion>
          <el-form
            ref="ruleFormRef"
            :model="ruleForm"
            :rules="loginRules"
            size="large"
          >
            <!-- 用户名 -->
            <Motion :delay="100">
              <el-form-item
                :rules="[
                  { required: true, message: '请输入账号', trigger: 'blur' }
                ]"
                prop="username"
              >
                <el-input
                  v-model="ruleForm.username"
                  clearable
                  placeholder="账号 (最少6位)"
                  :prefix-icon="useRenderIcon(User)"
                />
              </el-form-item>
            </Motion>

            <!-- 邮箱 (仅注册显示) -->
            <Motion :delay="120" v-if="isRegister">
              <el-form-item prop="email">
                <el-input
                  v-model="ruleForm.email"
                  clearable
                  placeholder="邮箱 (例如 student@zju.edu.cn)"
                  :prefix-icon="useRenderIcon(Mail)"
                />
              </el-form-item>
            </Motion>

            <!-- 密码 -->
            <Motion :delay="150">
              <el-form-item prop="password">
                <el-input
                  v-model="ruleForm.password"
                  clearable
                  show-password
                  placeholder="密码 (最少6位)"
                  :prefix-icon="useRenderIcon(Lock)"
                />
              </el-form-item>
            </Motion>

            <!-- 按钮区域 -->
            <Motion :delay="250">
              <el-button
                class="w-full mt-4!"
                size="default"
                type="primary"
                :loading="loading"
                @click="onSubmit(ruleFormRef)"
              >
                {{ isRegister ? "注册" : "登录" }}
              </el-button>
            </Motion>

            <!-- 切换链接 -->
            <Motion :delay="300">
              <div class="flex justify-between mt-4 text-sm text-gray-500">
                <!-- 占位，保持右对齐 -->
                <span />
                <el-link type="primary" :underline="false" @click="toggleMode">
                  {{ isRegister ? "已有账号？去登录" : "没有账号？去注册" }}
                </el-link>
              </div>
            </Motion>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url("@/style/login.css");
</style>

<style lang="scss" scoped>
:deep(.el-input-group__append, .el-input-group__prepend) {
  padding: 0;
}
/* 👇 [新增] 控制 logo 大小 */
.logo-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
/* 自定义logo大小*/
.custom-logo {
  width: 200px;
  height: 200px; /* 比例调整 */
  object-fit: contain;
}
</style>
