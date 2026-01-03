// 简单直接，不再引用报错的 /@@/utils
export default {
  path: "/image",
  name: "ImageManage",
  // 核心：必须指向 Layout 才能显示侧边栏框架
  component: () => import("@/layout/index.vue"),
  meta: {
    title: "图片管理",
    icon: "ep:picture",
    rank: 10
  },
  redirect: "/image/index",
  children: [
    {
      path: "/image/index",
      name: "ImageList",
      component: () => import("@/views/image/index.vue"),
      meta: {
        title: "图片列表",
        icon: "ep:list"
        // 关键点：如果依然不显示父级目录，确保这里没有把 showParent 设为 false
      }
    }
  ]
};
