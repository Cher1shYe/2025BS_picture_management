// 简单直接，不再引用报错的 /@@/utils
export default {
  path: "/gallery",
  name: "画廊展示",
  // 核心：必须指向 Layout 才能显示侧边栏框架
  component: () => import("@/layout/index.vue"),
  meta: {
    title: "画廊展示",
    icon: "ep:picture",
    rank: 5
  },
  redirect: "/gallery/index",
  children: [
    {
      path: "/gallery/index",
      name: "GalleryDisplay",
      component: () => import("@/views/gallery/index.vue"),
      meta: {
        title: "画廊展示",
        icon: "ep:picture-filled"
        // 关键点：如果依然不显示父级目录，确保这里没有把 showParent 设为 false
      }
    }
  ]
};
