import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 登录校验 */
const loginRules = reactive<FormRules>({
  password: [
    {
      validator: (rule, value, callback) => {
        if (value === "") {
          callback(new Error("请输入密码"));
        } else if (value.length < 6) {
          // [修改] 配合后端，只要大于6位即可，太复杂的正则在演示时容易出错
          callback(new Error("密码长度不能少于6位"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ],
  // [新增] 邮箱验证规则
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" }
  ]
});

export { loginRules };
