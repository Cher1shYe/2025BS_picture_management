# backend/app.py
import os
from flask import Flask
from exts import db
from dotenv import load_dotenv
from urllib.parse import quote_plus
from flask_cors import CORS  # [新增] 解决跨域问题

# 加载环境变量
load_dotenv()

# 引入蓝图
from controller.image import image_bp
# 引入初始化函数
from database import Initialize

def create_app():
    app = Flask(__name__)
    
    # --- 1. 解决跨域问题 ---
    # 允许所有域名访问，或者指定前端地址 supports_credentials=True
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --- 2. 数据库配置 ---
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME')
    
    # [优化] 检查环境变量是否存在，防止报错
    if not all([DB_USER, DB_PASSWORD, DB_NAME]):
        raise ValueError("请检查 .env 文件，数据库配置缺失！")

    # [关键] 处理密码中的特殊字符 (如 @, :, /)
    encoded_password = quote_plus(DB_PASSWORD)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    
    # --- 3. 上传文件配置 ---
    # 在这里统一配置，Controller里直接读取
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    # 限制最大上传大小 (例如 16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

    # --- 4. 初始化插件 ---
    db.init_app(app)
    
    # --- 5. 注册蓝图 ---
    app.register_blueprint(image_bp)
    
    # --- 6. 路由 ---
    @app.route('/')
    def hello():
        return "Photo System Backend is Running!"
        
    # --- 7. 数据库初始化逻辑 ---
    with app.app_context():
        # [注意] Initialize() 会清空数据库。
        # 建议仅在第一次运行或需要重置时开启，平时开发时注释掉，防止数据丢失。
        # Initialize() 
        pass 

    return app

if __name__ == '__main__':
    app = create_app()
    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    app.run(host='0.0.0.0', port=5001, debug=True)