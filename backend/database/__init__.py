import time
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()

from exts import db
from .models import User, Image, Tag

def Initialize():    
    # 1. 重置数据库
    print("正在重置数据库...")
    db.drop_all()
    db.create_all()
    
    # 2. 创建用户
    # 注意：实际生产中密码应该加密存储 (generate_password_hash)，这里为了演示先用明文
    admin = User("admin", "admin123", "admin@zju.edu.cn", role=0)
    user1 = User("student", "123456", "student@zju.edu.cn", role=1)
    
    db.session.add(admin)
    db.session.add(user1)
    db.session.commit() # 先提交以获取 uid
    
    # 3. 创建一些标签 (Tag)
    tags = [
        Tag("风景", "manual"),
        Tag("人像", "manual"),
        Tag("杭州", "exif"),
        Tag("AI:Cat", "ai"),
        Tag("浙大", "manual")
    ]
    for t in tags:
        db.session.add(t)
    db.session.commit()
    
    # 4. 创建假图片数据 (Image)
    # 假设我们有一个 uploads 文件夹
    
    # 图片 1: 属于 admin，带有 GPS 信息
    img1 = Image(
        uid=admin.uid,
        filename="demo1.jpg",
        original_name="my_photo.jpg",
        url="/static/assets/logo.png", # 暂时借用 logo 图片测试
        thumb_url="/static/assets/logo.png"
    )
    img1.shot_time = datetime(2023, 11, 1, 10, 30, 0)
    img1.location_str = "浙江大学紫金港校区"
    img1.latitude = 30.3068
    img1.longitude = 120.0863
    img1.camera_model = "iPhone 14 Pro"
    # 给图片打标签
    img1.tags.append(tags[2]) # 杭州
    img1.tags.append(tags[4]) # 浙大
    
    # 图片 2: 属于 student
    img2 = Image(
        uid=user1.uid,
        filename="cat.jpg",
        original_name="cute_cat.jpg",
        url="/static/assets/logo.png",
        thumb_url="/static/assets/logo.png"
    )
    img2.shot_time = datetime(2023, 11, 2, 14, 0, 0)
    img2.tags.append(tags[3]) # AI:Cat
    
    db.session.add(img1)
    db.session.add(img2)
    
    db.session.commit()
    print("数据库初始化完成！添加了 2 个用户，5 个标签，2 张测试图片。")