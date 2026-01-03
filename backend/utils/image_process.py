# backend/utils/image_process.py
import os
from PIL import Image, ExifTags

def make_thumbnail(source_path, target_path, size=(300, 300)):
    """
    生成缩略图
    :param source_path: 原图绝对路径
    :param target_path: 缩略图保存绝对路径
    :param size: 最大尺寸 (宽, 高)
    """
    try:
        with Image.open(source_path) as img:
            # 转换为 RGB (防止 PNG 透明背景转 JPG 报错)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 保持比例缩放
            img.thumbnail(size)
            img.save(target_path, "JPEG", quality=85)
            return True
    except Exception as e:
        print(f"缩略图生成失败: {e}")
        return False

def _to_decimal(value):
    """
    辅助：将 GPS (度, 分, 秒) 元组转为浮点数
    例如: ((30,1), (15,1), (0,1)) -> 30.25
    """
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except:
        return 0.0

def extract_exif(file_path):
    """
    提取信息以适配你的 Image 模型
    """
    data = {
        'shot_time': None,    # 对应 shot_time
        'camera_model': None, # 对应 camera_model
        'latitude': None,     # 对应 latitude (Float)
        'longitude': None,    # 对应 longitude (Float)
        'location_str': None  # 对应 location_str (String)
    }
    
    try:
        with Image.open(file_path) as img:
            exif_raw = img._getexif()
            if not exif_raw:
                return data

            # 转换 tag id 为名字
            exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_raw.items()}

            # 1. 拍摄时间
            # 通常格式: "YYYY:MM:DD HH:MM:SS"
            if 'DateTimeOriginal' in exif:
                data['shot_time'] = exif['DateTimeOriginal']
            elif 'DateTime' in exif:
                data['shot_time'] = exif['DateTime']

            # 2. 相机型号
            data['camera_model'] = exif.get('Model')

            # 3. GPS 处理 (核心逻辑)
            gps_info = exif.get('GPSInfo')
            if gps_info:
                # GPSInfo key: 1(N/S), 2(Lat), 3(E/W), 4(Lon)
                lat_ref = gps_info.get(1)
                lat_tuple = gps_info.get(2)
                lon_ref = gps_info.get(3)
                lon_tuple = gps_info.get(4)

                if lat_ref and lat_tuple and lon_ref and lon_tuple:
                    # 计算纬度 Float
                    lat = _to_decimal(lat_tuple)
                    if lat_ref == 'S': 
                        lat = -lat
                    
                    # 计算经度 Float
                    lon = _to_decimal(lon_tuple)
                    if lon_ref == 'W':
                        lon = -lon

                    data['latitude'] = lat
                    data['longitude'] = lon
                    
                    # 生成可读字符串，填入 location_str
                    data['location_str'] = f"{lat:.4f}, {lon:.4f}"

    except Exception as e:
        print(f"EXIF Error: {e}")
    
    return data