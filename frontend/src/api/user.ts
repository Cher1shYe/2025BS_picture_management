import { http } from "@/utils/http";

export type UserResult = {
  success: boolean;
  /** 后端返回的状态码 (例如 200, 400) - [新增] */
  code?: number;
  /** 后端返回的消息 (例如 "登录成功") - [新增] */
  msg?: string;
  data: {
    /** 用户名 */
    username: string;
    /** 当前登陆用户的角色 */
    roles: Array<string>; // 我们的后端是 role: int，前端可能需要转换，或者暂时不理会
    /** token */
    accessToken: string;
    /** 用于调用刷新accessToken的接口时所需的token */
    refreshToken: string;
    /** accessToken的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;

    // 新增
    /** 邮箱 */
    email?: string;
    /** 头像地址 */
    avatar?: string;
  };
};

export type RefreshTokenResult = {
  success: boolean;
  data: {
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;
  };
};

/** 登录 */
export const getLogin = (data?: object) => {
  // 注意：这里改成后端路由 /api/auth/login
  return http.request<UserResult>("post", "/api/auth/login", { data });
};

export const getRegister = (data?: object) => {
  return http.request<UserResult>("post", "/api/auth/register", { data });
};

/** 刷新`token` (可选，大作业暂时用不到可以先放着) */
export const refreshTokenApi = (data?: object) => {
  return http.request<RefreshTokenResult>("post", "/refresh-token", { data });
};

/** 获取用户信息 */
export const getUserInfo = () => {
  return http.request<UserResult>("get", "/api/user/info");
};

/** 修改基本信息 */
export const updateUserInfo = (data: object) => {
  return http.request<UserResult>("post", "/api/user/update/info", { data });
};

/** 修改密码 */
export const updateUserPassword = (data: object) => {
  return http.request<UserResult>("post", "/api/user/update/password", {
    data
  });
};

/** 上传头像 (注意这里 Content-Type 不一样，但 axios 通常会自动处理 FormData) */
export const uploadAvatarApi = (params: any) => {
  return http.request<UserResult>("post", "/api/user/update/avatar", {
    headers: { "Content-Type": "multipart/form-data" },
    params // PureAdmin 的 http 封装如果传 FormData 可能需要特殊处理，下面页面代码里我会用原生 axios 或调整写法
  });
};

/** 注销 */
export const getLogout = () => {
  return http.request<UserResult>("post", "/api/auth/logout");
};
