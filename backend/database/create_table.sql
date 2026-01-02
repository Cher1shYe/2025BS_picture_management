/*
 SQL 脚本: 图片管理系统初始化
 对应后端 models.py 的结构
*/

-- 1. 如果不存在则创建数据库，并切换
CREATE DATABASE IF NOT EXISTS photo_sys CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE photo_sys;

-- 为了防止外键报错，先暂时关闭外键检查，或者按顺序删除旧表
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS image_tags;
DROP TABLE IF EXISTS image;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS user;
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- 2. 创建用户表 (User)
-- ----------------------------
CREATE TABLE `user` (
  `uid` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(255) NOT NULL COMMENT '密码(加密后)',
  `email` varchar(100) NOT NULL COMMENT '邮箱',
  `role` int DEFAULT 1 COMMENT '角色 0:admin, 1:user',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  PRIMARY KEY (`uid`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 3. 创建标签表 (Tag)
-- ----------------------------
CREATE TABLE `tag` (
  `tid` int NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name` varchar(50) NOT NULL COMMENT '标签名',
  `type` varchar(20) DEFAULT 'manual' COMMENT '类型: manual, ai, exif',
  PRIMARY KEY (`tid`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 4. 创建图片表 (Image)
-- ----------------------------
CREATE TABLE `image` (
  `iid` int NOT NULL AUTO_INCREMENT COMMENT '图片ID',
  `uid` int NOT NULL COMMENT '所属用户ID',
  `filename` varchar(255) NOT NULL COMMENT '存储文件名',
  `original_name` varchar(255) NOT NULL COMMENT '原始文件名',
  `file_size` int DEFAULT 0 COMMENT '文件大小(KB)',
  `url` varchar(255) NOT NULL COMMENT '访问路径',
  `thumb_url` varchar(255) DEFAULT NULL COMMENT '缩略图路径',
  
  -- EXIF 信息
  `shot_time` datetime DEFAULT NULL COMMENT '拍摄时间',
  `location_str` varchar(255) DEFAULT NULL COMMENT '地点文字',
  `latitude` float DEFAULT NULL COMMENT '纬度',
  `longitude` float DEFAULT NULL COMMENT '经度',
  `camera_model` varchar(100) DEFAULT NULL COMMENT '相机型号',
  
  `upload_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  PRIMARY KEY (`iid`),
  KEY `idx_uid` (`uid`),
  CONSTRAINT `fk_image_user` FOREIGN KEY (`uid`) REFERENCES `user` (`uid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 5. 创建图片-标签关联表 (image_tags)
-- 多对多关系
-- ----------------------------
CREATE TABLE `image_tags` (
  `image_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`image_id`, `tag_id`),
  KEY `idx_tag_id` (`tag_id`),
  CONSTRAINT `fk_map_image` FOREIGN KEY (`image_id`) REFERENCES `image` (`iid`) ON DELETE CASCADE,
  CONSTRAINT `fk_map_tag` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`tid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 6. (可选) 插入一个测试管理员账号
-- 密码是 'admin123' 的哈希值 (pbkdf2:sha256...)
-- ----------------------------
INSERT INTO `user` (`username`, `password`, `email`, `role`) 
VALUES ('admin', 'pbkdf2:sha256:600000$YourHashHere...', 'admin@zju.edu.cn', 0);