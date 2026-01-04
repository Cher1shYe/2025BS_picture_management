# 阶段 1: 构建
FROM node:20-alpine as build-stage

WORKDIR /app
RUN corepack enable
RUN corepack prepare pnpm@latest --activate

# 设置镜像源
RUN npm config set registry https://registry.npmmirror.com

COPY .npmrc package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# 优化点：为 Pure Admin 构建增加内存限制，防止 OOM 导致构建中断
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN pnpm build

# 阶段 2: 运行
FROM nginx:stable-alpine as production-stage

# 复制编译产物
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 核心改进：复制自定义的 nginx 配置文件，覆盖镜像默认配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]