# services/ai_model.py
import os
from PIL import Image
from transformers import pipeline

# 全局变量缓存模型，防止每次请求都重新加载（很慢）
classifier = None

def get_image_tags(image_path):
    """
    输入图片路径，返回识别到的标签列表 (英文 -> 可以自己做个简单的映射转中文)
    """
    global classifier
    
    # 懒加载模式：第一次调用时才下载/加载模型
    if classifier is None:
        print("正在加载 AI 模型 (第一次可能比较慢)...")
        # 苹果电脑用mps
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"当前运行设备: {device.upper()}")

        # 加载模型，指定 device
        classifier = pipeline(
            "image-classification", 
            model="google/vit-base-patch16-224",
            device=device 
        )
        # 使用 Google 的 Vision Transformer，效果好且速度尚可
        classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

    try:
        # 进行预测，获取前 5 个可能的结果
        results = classifier(image_path, top_k=5)
        
        # 提取标签，过滤掉置信度低于 10% 的
        tags = [res['label'].split(',')[0] for res in results if res['score'] > 0.1]
        
        return list(set(tags)) # 去重

    except Exception as e:
        print(f"AI 分析失败: {e}")
        return []