# backend/controller/auth.py
import re
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
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    # 1. 基础非空校验
    if not all([username, password, email]):
        return jsonify({'code': 400, 'msg': '请填写完整信息'}), 400

    # 2. 长度校验
    if len(username) < 6:
        return jsonify({'code': 400, 'msg': '用户名长度必须大于6位'}), 400
    if len(password) < 6:
        return jsonify({'code': 400, 'msg': '密码长度必须大于6位'}), 400

    # 3. 邮箱格式校验
    try:
        validate_email(email)
    except EmailNotValidError:
        return jsonify({'code': 400, 'msg': '邮箱格式不正确'}), 400

    # 4. 唯一性校验 (查库)
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'code': 400, 'msg': '邮箱已被注册'}), 400

    # 5. 创建用户 (密码一定要加密存储！)
    # generate_password_hash 会把 "123456" 变成 "pbkdf2:sha256:..." 这种乱码
    new_user = User(
        username=username,
        password=generate_password_hash(password), 
        email=email,
        role=1
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '注册成功，请登录', 'data': {'uid': new_user.uid}})


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
    # check_password_hash 会自动把用户输入的明文和数据库里的密文比对
    if user and check_password_hash(user.password, password):
        
        # 3. 生成 Token (这就是用户的身份证，有效期默认15分钟，可配置)
        # identity 可以存 uid，这样后续接口就能知道是谁在操作
        access_token = create_access_token(identity=user.uid)
        
        return jsonify({
            'code': 200, 
            'msg': '登录成功',
            'data': {
                'accessToken': access_token, # 前端要把这个存起来
                'username': user.username,
                'role': user.role
            }
        })
    else:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401