import os

# 设置镜像源，必须放在 import transformers 之前
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import torch
from PIL import Image
from transformers import pipeline

classifier = None

def get_image_tags(image_path):
    global classifier
    
    if classifier is None:
        print("正在从国内镜像加载 AI 模型...")
        
        # 苹果 M1/M2 芯片使用 mps
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        
        # 加载模型 (修复了你原本代码里重复加载的逻辑)
        classifier = pipeline(
            "image-classification", 
            model="google/vit-base-patch16-224",
            device=device
        )
        print(f"模型加载成功，运行设备: {device.upper()}")

    try:
        # 识别图片
        results = classifier(image_path, top_k=5)
        
        # 提取标签，过滤掉置信度低于 10% 的
        tags = [res['label'].split(',')[0] for res in results if res['score'] > 0.1]
        
        return list(set(tags))

    except Exception as e:
        print(f"AI 分析失败: {e}")
        return []