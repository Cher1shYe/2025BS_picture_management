const { VITE_HIDE_HOME } = import.meta.env;
const Layout = () => import("@/layout/index.vue");

export default {
  path: "/",
  name: "Home",
  component: Layout,
  redirect: "/welcome",
  meta: {
    icon: "ep/home-filled",
    title: "首页",
    rank: 0
  },
  children: [
    {
      path: "/welcome",
      name: "Welcome",
      component: () => import("@/views/welcome/index.vue"),
      meta: {
        title: "首页",
        showLink: VITE_HIDE_HOME === "true" ? false : true
      }
    },
    {
      path: "/person",
      name: "Person",
      component: () => import("@/views/person/index.vue"),
      meta: {
        title: "个人中心",
        icon: "ep:user", // 需要确保图标库有这个
        showLink: true
      }
    }
  ]
} satisfies RouteConfigsTable;
