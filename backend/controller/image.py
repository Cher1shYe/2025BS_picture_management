# backend/controller/image.py
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from database.models import Image, Tag
from utils.image_process import make_thumbnail, extract_exif
from datetime import datetime # 处理时间

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

    # [新增] 缩略图路径 (在 uploads 下创建一个 thumbs 文件夹)
    thumb_dir = os.path.join(upload_dir, 'thumbs')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    thumb_path = os.path.join(thumb_dir, unique_filename)
    
    # 5. 保存文件到磁盘
    try:
        file.save(save_path)

        # 生成缩略图
        has_thumb = make_thumbnail(save_path, thumb_path)

        # 提取 EXIF 信息
        exif = extract_exif(save_path)

        # 解析拍摄时间 (字符串 -> datetime 对象)
        shot_time_obj = None
        if exif['shot_time']:
            try:
                # 尝试解析常见的 EXIF 时间格式
                shot_time_obj = datetime.strptime(exif['shot_time'], '%Y:%m:%d %H:%M:%S')
            except:
                pass # 解析失败就留空，不影响上传

        
        # 6. 写入数据库
        # 生成访问 URL (前端通过这个 URL 这里的 /static/.. 访问图片)
        url_path = f"/static/uploads/{unique_filename}"

        # 如果生成了缩略图，就用缩略图路径，否则用原图
        thumb_url_path = f"/static/uploads/thumbs/{unique_filename}" if has_thumb else url_path
        
        new_img = Image(
            uid=current_uid,
            filename=unique_filename,
            original_name=original_name,
            url=url_path,
            thumb_url=thumb_url_path # [修改] 把原图变成缩略图
        )
        new_img.file_size = os.path.getsize(save_path) // 1024 # KB

        # [新增] 填入 EXIF 数据 (对应你的 models.py 字段)
        new_img.shot_time = shot_time_obj
        new_img.camera_model = exif['camera_model']
        new_img.location_str = exif['location_str']
        new_img.latitude = exif['latitude']
        new_img.longitude = exif['longitude']

        # [新增] 自动标签逻辑 (按年份)
        if shot_time_obj:
            year_tag_name = f"{shot_time_obj.year}年"
            
            # 查一下库里有没有这个年份标签
            tag = Tag.query.filter_by(name=year_tag_name).first()
            if not tag:
                # 没有就创建一个，类型标记为 exif
                tag = Tag(name=year_tag_name, type='exif')
                db.session.add(tag)
            
            # 把标签贴到图片上
            new_img.tags.append(tag)
        
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

    # 2. 获取高级筛选参数
    tag_id = request.args.get('tag_id', type=int) # 按标签ID筛选
    start_date = request.args.get('start_date', type=str) # 格式 'YYYY-MM-DD'
    end_date = request.args.get('end_date', type=str)     # 格式 'YYYY-MM-DD'

    # 3. 获取文件名和地点搜索关键词
    keyword = request.args.get('keyword', '', type=str)   # 仅用于搜索文件名
    location = request.args.get('location', '', type=str) # 【新增】专门搜索地点
    
    base_url = request.host_url.rstrip('/')

    # [修复2] 构建查询（过滤用户）
    query = Image.query.filter_by(uid=current_uid)
    
    # 如果有搜索关键词，就在 original_name 或 location_str 里找
    if keyword:
        query = query.filter(
            or_(
                Image.original_name.like(f'%{keyword}%'),
            )
        )
    # 【新增】按标签筛选
    if tag_id:
        # join Image.tags 关系字段，找到包含该 tag_id 的图片
        query = query.join(Image.tags).filter(Tag.tid == tag_id)
    
    # 【新增】地点搜索 (基于 EXIF location_str 字段)
    if location:
        query = query.filter(Image.location_str.ilike(f'%{location}%'))
    # 按时间倒序排列 (最新的在前)
    query = query.order_by(Image.upload_time.desc())

    # 【新增】按时间范围筛选 (优先用 shot_time，没有则用 upload_time)
    # 这里稍微简化，只筛选 shot_time，实际业务中可以用 coalesce
    if start_date and end_date:
        try:
            # 转换字符串为日期对象，注意 end_date 要加一天或设为当晚23:59:59
            s_date = datetime.strptime(start_date, '%Y-%m-%d')
            e_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            
            query = query.filter(
                Image.shot_time.between(s_date, e_date)
            )
        except ValueError:
            pass # 日期格式不对就不筛了
    

    # 排序与分页
    pagination = query.order_by(Image.upload_time.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    
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

# =========== 【新增】给图片添加自定义标签 ===========
@image_bp.route('/add_tag', methods=['POST'])
@jwt_required()
def add_tag_to_image():
    data = request.json
    image_id = data.get('image_id')
    tag_name = data.get('tag_name')

    if not image_id or not tag_name:
        return jsonify({'code': 400, 'msg': '参数不全'}), 400

    current_uid = get_jwt_identity()
    
    # 1. 确认图片属于该用户
    img = Image.query.filter_by(iid=image_id, uid=current_uid).first()
    if not img:
        return jsonify({'code': 404, 'msg': '图片不存在'}), 404

    # 2. 处理标签
    tag_name = tag_name.strip()
    # 查库看标签是否已存在
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        # 不存在则新建 (类型 manual)
        tag = Tag(name=tag_name, type='manual')
        db.session.add(tag)
        db.session.flush() # 刷新以获取 tag.tid
    
    # 3. 建立关联 (如果还没关联的话)
    if tag not in img.tags:
        img.tags.append(tag)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '标签添加成功'})
    else:
        return jsonify({'code': 200, 'msg': '标签已存在'})
    
# =========== 【新增】获取系统所有标签 (用于前端下拉筛选，非必要，做着玩) ===========
@image_bp.route('/all_tags', methods=['GET'])
@jwt_required()
def get_all_tags():
    # 这里简单处理：返回数据库里所有的标签
    # 进阶做法是：只返回当前用户用过的标签 (需要连表查询)，为了演示简单，先取全部
    tags = Tag.query.all()
    tag_list = [{'id': t.tid, 'name': t.name} for t in tags]
    return jsonify({'code': 200, 'data': tag_list})

# =========== 【新增】删除图片接口 ===========
@image_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_image():
    # 1. 获取参数
    data = request.json
    image_id = data.get('id')

    if not image_id:
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    # 2. 获取当前用户
    current_uid = get_jwt_identity()

    # 3. 查库：必须同时满足 ID存在 且 是当前用户的图
    img = Image.query.filter_by(iid=image_id, uid=current_uid).first()
    
    if not img:
        return jsonify({'code': 404, 'msg': '图片不存在或无权删除'}), 404

    try:
        # 4. 定位物理文件路径 (完全复用 upload 的路径逻辑)
        # 从配置中读取上传根目录
        upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # 拼接原图路径
        file_path = os.path.join(upload_dir, img.filename)
        
        # 拼接缩略图路径 (假设之前的逻辑是存放在 thumbs 子目录下)
        # 如果你之前的 upload 没生成 thumbs 目录，这段代码也不会报错，因为有 exists 判断
        thumb_path = os.path.join(upload_dir, 'thumbs', img.filename)

        # 5. 删除物理文件
        # 删除原图
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"已删除文件: {file_path}")
        else:
            print(f"文件未找到(可能已被删): {file_path}")

        # 删除缩略图
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        # 6. 删除数据库记录
        db.session.delete(img)
        db.session.commit()

        return jsonify({'code': 200, 'msg': '删除成功'})

    except Exception as e:
        print(f"删除失败: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败: ' + str(e)}), 500
    
# =========== 【新增】移除图片的标签 ===========
@image_bp.route('/remove_tag', methods=['POST'])
@jwt_required()
def remove_tag_from_image():
    data = request.json
    image_id = data.get('image_id')
    tag_name = data.get('tag_name') # 前端传标签名过来

    if not image_id or not tag_name:
        return jsonify({'code': 400, 'msg': '参数不全'}), 400

    current_uid = get_jwt_identity()
    
    # 1. 查找图片 (确保是自己的)
    img = Image.query.filter_by(iid=image_id, uid=current_uid).first()
    if not img:
        return jsonify({'code': 404, 'msg': '图片不存在'}), 404

    # 2. 查找标签
    tag = Tag.query.filter_by(name=tag_name).first()
    
    # 3. 移除关联
    if tag and tag in img.tags:
        img.tags.remove(tag)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '标签移除成功'})
    else:
        return jsonify({'code': 400, 'msg': '标签未关联或不存在'})