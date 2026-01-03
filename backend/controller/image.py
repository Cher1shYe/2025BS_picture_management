# backend/controller/image.py
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

# 引用我们刚刚定义的 db 和模型
from exts import db
from database.models import Image, Tag, User

# 定义蓝图，访问地址前缀为 /api/image
image_bp = Blueprint('image', __name__, url_prefix='/api/image')

# 1. 图片上传接口
# 访问方式: POST http://localhost:5001/api/image/upload
# 参数: form-data key='file'
@image_bp.route('/upload', methods=['POST'])
@jwt_required() # [修复] 必须登录才能传
def upload_image():
    # 1. 检查有没有文件 
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '文件名为空'}), 400

    # 2.[修复] 获取当前用户 (做了登录后再换成了 current_user.uid)
    current_uid = get_jwt_identity()

    # 3. 生成安全的文件名 (防止文件名冲突或中文乱码)
    # 例如: my_photo.jpg -> a1b2c3d4.jpg
    original_name = file.filename
    ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'jpg'
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # 4. 确定保存路径
    # 假设保存在 backend/static/uploads 目录下
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    save_path = os.path.join(upload_dir, unique_filename)
    
    # 5. 保存文件到磁盘
    try:
        file.save(save_path)
        
        # TODO: 这里未来要加入: 
        # 1. 生成缩略图 
        # 2. 提取 EXIF 信息
        # 暂时先填默认值
        
        # 6. 写入数据库
        # 生成访问 URL (前端通过这个 URL 这里的 /static/.. 访问图片)
        url_path = f"/static/uploads/{unique_filename}"
        
        new_img = Image(
            uid=current_uid,
            filename=unique_filename,
            original_name=original_name,
            url=url_path,
            thumb_url=url_path # 暂时用原图当缩略图
        )
        new_img.file_size = os.path.getsize(save_path) // 1024 # KB
        
        db.session.add(new_img)
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '上传成功', 
            'data': {
                'id': new_img.iid,
                'url': new_img.url
            }
        })

    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'msg': '上传失败: ' + str(e)}), 500


# 2. 获取图片列表接口 (支持搜索、分页)
# 访问方式: GET http://localhost:5001/api/image/list?page=1&limit=20&keyword=杭州
@image_bp.route('/list', methods=['GET'])
@jwt_required() # [修复1] 必须登录
def get_image_list():
    current_uid = get_jwt_identity()
    # 获取参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    keyword = request.args.get('keyword', '', type=str)
    
    base_url = request.host_url.rstrip('/')

    # [修复2] 构建查询（过滤用户）
    query = Image.query.filter_by(uid=current_uid)
    
    # 如果有搜索关键词，就在 original_name 或 location_str 里找
    if keyword:
        query = query.filter(
            or_(
                Image.original_name.like(f'%{keyword}%'),
                Image.location_str.like(f'%{keyword}%'),
                # 甚至可以搜索标签 (稍微复杂点，先放着)
            )
        )
    
    # 按时间倒序排列 (最新的在前)
    query = query.order_by(Image.upload_time.desc())
    
    # 执行分页
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    # 格式化返回数据
    img_list = []
    for img in pagination.items:
        full_url = f"{base_url}{img.url}"
        full_thumb = f"{base_url}{img.thumb_url}"
        img_list.append({
            'id': img.iid,
            'name': img.original_name,
            'url': full_url,
            'thumb': full_thumb,
            'date': img.shot_time.strftime('%Y-%m-%d') if img.shot_time else img.upload_time.strftime('%Y-%m-%d'),
            'location': img.location_str,
            'tags': [t.name for t in img.tags]
        })
        
    return jsonify({
        'code': 200,
        'msg': 'success',
        'data': {
            'total': pagination.total,
            'items': img_list
        }
    })