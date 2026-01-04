# backend/controller/user.py
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from exts import db
from database.models import User

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. 获取当前用户信息 ---
@user_bp.route('/info', methods=['GET'])
@jwt_required()
def get_user_info():
    uid = get_jwt_identity()
    user = db.session.get(User, uid)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在', 'success': False})
    
    # 拼接完整的头像 URL
    avatar_url = ""
    if user.avatar:
        # 假设我们通过 static 目录访问
        avatar_url = url_for('static', filename=f'uploads/avatars/{user.avatar}', _external=True)
    
    return jsonify({
        'code': 200,
        'success': True,
        'data': {
            'username': user.username,
            'email': user.email,
            'avatar': avatar_url,
            'roles': ['admin'] if user.role == 0 else ['common']
        }
    })

# --2. 修改用户信息 ---
@user_bp.route('/update/info', methods=['POST'])
@jwt_required()
def update_info():
    uid = get_jwt_identity()
    user = db.session.get(User, uid)
    
    # 获取 JSON 数据里的 data 字段 (因为前端可能是包装在 {data: {...}} 里发的)
    # 或者前端直接发的就是 {...}
    # 我们做一个兼容处理
    req_json = request.json
    # 如果前端用了 axios 封装，可能会多包一层 data，如果没包，直接用 req_json
    data = req_json.get('data') if 'data' in req_json else req_json
    
    print(f"收到更新请求: {data}") # [后端调试] 看看终端里打印了什么

    new_username = data.get('username')
    new_email = data.get('email')
    
    # --- 关键修改：更稳健的更新逻辑 ---
    
    # 1. 只有当 new_username 存在且不为空字符串时才更新
    if new_username and new_username.strip():
        # 简单查重：如果改了名，且名字被别人用了
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.uid != user.uid:
             return jsonify({'code': 400, 'success': False, 'msg': '该用户名已被占用'}), 400
        user.username = new_username

    # 2. 只有当 new_email 存在时才更新 (允许改为空)
    if new_email is not None:
        user.email = new_email

    try:
        db.session.commit()
        return jsonify({
            'code': 200, 
            'success': True, 
            'msg': '信息更新成功',
            'data': { # 把更新后的数据返给前端，方便前端刷新
                'username': user.username,
                'email': user.email
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'msg': f'数据库错误: {str(e)}'}), 500

# --- 3. 修改密码 ---
@user_bp.route('/update/password', methods=['POST'])
@jwt_required()
def update_password():
    try:
        uid = get_jwt_identity()
        user = db.session.get(User, uid)
        
        # 兼容处理：获取前端传来的数据
        req_json = request.json
        data = req_json.get('data') if req_json and 'data' in req_json else req_json
        
        old_pass = data.get('oldPassword')
        new_pass = data.get('newPassword')
        
        # 1. 简单校验
        if not old_pass or not new_pass:
            return jsonify({'code': 400, 'success': False, 'msg': '参数不完整'}), 400
        
        if len(new_pass) < 6:
            return jsonify({'code': 400, 'success': False, 'msg': '新密码长度不能少于6位'}), 400
        
        # 2. 校验旧密码
        if not check_password_hash(user.password, old_pass):
            return jsonify({'code': 400, 'success': False, 'msg': '旧密码不正确'}), 400
            
        # 3. 加密新密码 [关键修复点]
        # 必须加上 method='pbkdf2:sha256'
        hashed_password = generate_password_hash(new_pass, method='pbkdf2:sha256')
        
        user.password = hashed_password
        db.session.commit()
        
        return jsonify({'code': 200, 'success': True, 'msg': '密码修改成功，请重新登录'})

    except Exception as e:
        print(f"修改密码报错: {str(e)}") # 打印错误到终端方便调试
        db.session.rollback()
        return jsonify({'code': 500, 'success': False, 'msg': '服务器内部错误'}), 500

# --- 4. 上传/修改头像 ---
@user_bp.route('/update/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '没有文件上传', 'success': False})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件', 'success': False})
        
    if file and allowed_file(file.filename):
        # 生成随机文件名，防止重名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = str(uuid.uuid4()) + "." + ext
        
        save_path = os.path.join(current_app.config['AVATAR_UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # 更新数据库
        uid = get_jwt_identity()
        user = db.session.get(User, uid)
        user.avatar = filename
        db.session.commit()
        
        full_url = url_for('static', filename=f'uploads/avatars/{filename}', _external=True)
        
        return jsonify({'code': 200, 'success': True, 'msg': '头像上传成功', 'data': {'avatar': full_url}})
    
    return jsonify({'code': 400, 'msg': '不支持的文件格式', 'success': False})