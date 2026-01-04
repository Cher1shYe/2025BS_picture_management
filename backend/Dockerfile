FROM python:3.12-slim

# 新增：更换 Debian 软件源为阿里云 (适用于 Debian 13/trixie)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装依赖
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制后端源码
COPY . .

# 创建上传文件夹和缩略图文件夹
RUN mkdir -p static/uploads/thumbs

# 暴露 Flask 端口 (假设你代码里是 5001)
EXPOSE 5001

# 使用 gunicorn 运行生产环境，或者直接 python app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]