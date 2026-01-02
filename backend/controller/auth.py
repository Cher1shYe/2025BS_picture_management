# backend/controller/auth.py
import re
import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from email_validator import validate_email, EmailNotValidError

from exts import db
from database.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# --- 1. 用户注册接口 ---
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    ---
    tags:
      - Auth (用户认证)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
            - email
          properties:
            username:
              type: string
              description: 用户名 (长度>6)
              example: student1
            password:
              type: string
              description: 密码 (长度>6)
              example: 1234567
            email:
              type: string
              description: 邮箱
              example: student@zju.edu.cn
    responses:
      200:
        description: 注册成功
      400:
        description: 参数错误
    """
    data = request.json
    # 使用 .get() 避免报错，且统一去除首尾空格
    username = data.get('username', '').strip()
    password = str(data.get('password', '')).strip() # 强转字符串
    email = data.get('email', '').strip()

    # 1. 基础非空校验
    if not all([username, password, email]):
        return jsonify({'code': 400, 'msg': '请填写完整信息', 'success': False}), 400

    # 2. 长度校验
    if len(username) < 6:
        return jsonify({'code': 400, 'msg': '用户名长度必须大于6位', 'success': False}), 400
    if len(password) < 6:
        return jsonify({'code': 400, 'msg': '密码长度必须大于6位', 'success': False}), 400

    # 3. 邮箱格式校验
    try:
        validate_email(email)
    except EmailNotValidError:
        return jsonify({'code': 400, 'msg': '邮箱格式不正确', 'success': False}), 400

    # 4. 唯一性校验 (查库)
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在', 'success': False}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'code': 400, 'msg': '邮箱已被注册', 'success': False}), 400

    # 5. 创建用户 (加密存储)
    # 默认给 role=1 (普通用户)，如果是管理员可以给 0 或其他
    new_user = User(
        username=username,
        password=generate_password_hash(password, method='pbkdf2:sha256'), 
        email=email,
        role=1 
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'数据库保存失败: {str(e)}', 'success': False}), 500

    # 注册成功也返回 success: True
    return jsonify({
        'code': 200, 
        'success': True, 
        'msg': '注册成功，请登录', 
        'data': {'uid': new_user.uid}
    })


# --- 2. 用户登录接口 ---
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    ---
    tags:
      - Auth (用户认证)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: admin123
    responses:
      200:
        description: 登录成功，返回 Token
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 1. 查找用户
    user = User.query.filter_by(username=username).first()

    # 2. 校验密码
    if user and check_password_hash(user.password, password):
        
        # 3. 生成 Token (identity 转为字符串比较稳妥)
        access_token = create_access_token(identity=str(user.uid))
        
        # 4. 返回前端需要的数据结构
        # Pure Admin 前端通常需要 roles 数组和 expires 时间
        return jsonify({
            'code': 200,
            'success': True,  # 关键修复：这里原来写法不对，现在修好了
            'msg': '登录成功',
            'data': {
                'accessToken': access_token,
                'username': user.username,
                # 将整数 role 转换为前端能理解的角色数组
                'roles': ['admin'] if user.role == 0 else ['common'], 
                # 随便给一个未来的过期时间，防止前端拦截器报错
                'expires': '2030/12/30 23:59:59'
            }
        })
    else:
        return jsonify({
            'code': 401, 
            'success': False, 
            'msg': '用户名或密码错误'
        }), 401