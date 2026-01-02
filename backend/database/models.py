from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Table
from datetime import datetime
from exts import db

# 关联表：用于连接 Image 和 Tag (多对多关系)
image_tags = Table(
    'image_tags',
    db.metadata,
    db.Column('image_id', Integer, ForeignKey('image.iid'), primary_key=True),
    db.Column('tag_id', Integer, ForeignKey('tag.tid'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    uid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False) # 建议存储哈希值
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    role: Mapped[int] = mapped_column(Integer, default=1) # 0: admin, 1: user
    # 新增：头像管理
    avatar: Mapped[str] = mapped_column(db.String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # 关系：一个用户可以有多张图片
    images = relationship("Image", back_populates="owner", cascade="all, delete-orphan")

    def __init__(self, username, password, email, role=1):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
    
    def __repr__(self):
        return f'<User {self.username}>'

class Tag(db.Model):
    __tablename__ = 'tag'
    tid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # 类型：manual(手动), ai(AI识别), exif(自动提取)
    type: Mapped[str] = mapped_column(String(20), default='manual') 

    def __init__(self, name, type='manual'):
        self.name = name
        self.type = type

class Image(db.Model):
    __tablename__ = 'image'
    iid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 基础文件信息
    filename: Mapped[str] = mapped_column(String(255), nullable=False) # 存储在磁盘上的唯一文件名
    original_name: Mapped[str] = mapped_column(String(255), nullable=False) # 用户上传时的文件名
    file_size: Mapped[int] = mapped_column(Integer, nullable=True) # KB
    
    # URL 路径
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    thumb_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # EXIF 信息 (自动提取)
    shot_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    location_str: Mapped[str] = mapped_column(String(255), nullable=True) # 如 "杭州市, 浙江省"
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    camera_model: Mapped[str] = mapped_column(String(100), nullable=True)
    
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # 外键：关联用户
    uid: Mapped[int] = mapped_column(Integer, ForeignKey('user.uid'), nullable=False)
    owner = relationship("User", back_populates="images")
    
    # 关系：多对多关联标签
    tags = relationship("Tag", secondary=image_tags, backref="images")

    def __init__(self, uid, filename, original_name, url, thumb_url=None):
        self.uid = uid
        self.filename = filename
        self.original_name = original_name
        self.url = url
        self.thumb_url = thumb_url