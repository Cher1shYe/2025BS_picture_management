# controller/ai.py
from flask import Blueprint, jsonify, request
from exts import db
from database.models import Image, Tag
from services.ai_model import get_image_tags
from flask_jwt_extended import jwt_required, get_jwt_identity

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/analyze/<int:image_id>', methods=['POST'])
@jwt_required()
def analyze_image(image_id):
    # 1. 找图片
    img = Image.query.get(image_id)
    if not img:
        return jsonify({'code': 404, 'msg': '图片不存在'}), 404
        
    # 2. 获取物理路径 (假设你的 current_app 配置里有 static_folder)
    # 或者直接拼接: backend/static/uploads/文件名
    file_path = os.path.join('static/uploads', img.filename)
    
    if not os.path.exists(file_path):
        return jsonify({'code': 400, 'msg': '物理文件丢失'}), 400
        
    # 3. 调用 AI 分析
    ai_tags = get_image_tags(file_path)
    
    if not ai_tags:
        return jsonify({'code': 200, 'msg': 'AI 未识别出明显特征', 'data': []})

    # 4. 将标签存入数据库
    added_tags = []
    for tag_name in ai_tags:
        # 查找 tag 是否存在，不存在则创建
        tag_obj = Tag.query.filter_by(name=tag_name).first()
        if not tag_obj:
            tag_obj = Tag(name=tag_name, type='ai') # 标记为 AI 生成
            db.session.add(tag_obj)
            db.session.flush() # 获取 ID
            
        # 建立关联 (如果还没关联)
        if tag_obj not in img.tags:
            img.tags.append(tag_obj)
            added_tags.append(tag_name)
            
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': 'AI 分析完成', 
        'data': added_tags
    })