# backend/app.py
import os
from flask import Flask
from exts import db
from dotenv import load_dotenv
from urllib.parse import quote_plus
from flask_cors import CORS
from flasgger import Swagger  # [新增]
from flask_jwt_extended import JWTManager # [新增]

# 引入蓝图
from controller.image import image_bp
from controller.auth import auth_bp # [新增] 还没写，马上写
from controller.user import user_bp # [新增] 用户信息相关接口
from database import Initialize

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # --- 1. 基础配置 ---
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME')
    
    encoded_password = quote_plus(DB_PASSWORD)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')
    
    # --- [新增] Swagger 配置 ---
    app.config['SWAGGER'] = {
        'title': '图片管理系统 API',
        'uiversion': 3
    }
    # 初始化 Swagger, 访问地址: http://localhost:5001/apidocs
    Swagger(app)

    # --- [新增] JWT 配置 ---
    app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret') # 用于加密 Token
    JWTManager(app)

    # --- 文件上传配置 ---
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # --- 初始化 ---
    db.init_app(app)
    
    # --- 注册蓝图 ---
    app.register_blueprint(image_bp)
    app.register_blueprint(auth_bp) # [新增] 注册 Auth 蓝图
    app.register_blueprint(user_bp) # [新增] User信息处理蓝图

    # [新增] 配置上传文件夹
    # 存放在 backend/static/uploads/avatars 下
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'avatars')
    
    # 如果文件夹不存在，自动创建
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    return app

if __name__ == '__main__':
    app = create_app()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5001, debug=True)