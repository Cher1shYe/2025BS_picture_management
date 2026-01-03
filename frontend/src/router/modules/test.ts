export default {
  path: "/test",
  redirect: "/test/index",
  meta: {
    icon: "ri/information-line",
    // showLink: false,
    title: "测试页面",
    rank: 100
  },
  children: [
    {
      path: "/test/index",
      name: "Test",
      component: () => import("@/views/Test.vue"),
      meta: {
        title: "测试页面"
      }
    }
  ]
} satisfies RouteConfigsTable;
