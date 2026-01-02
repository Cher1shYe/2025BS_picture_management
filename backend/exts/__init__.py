# backend/exts/__init__.py
from flask_sqlalchemy import SQLAlchemy

# 这里只创建对象，暂时不绑定具体的 app，等到 app.py 启动时再绑定
db = SQLAlchemy()