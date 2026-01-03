# mcp_server.py
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json

load_dotenv() 

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 初始化 MCP 服务
mcp = FastMCP("PhotoSystem Gallery")

engine = create_engine(DB_URI)

@mcp.tool()
def search_images(keyword: str = None, date_start: str = None, limit: int = 5):
    """
    Search for images in the gallery database.
    
    Args:
        keyword: Search term for tags (e.g., "cat", "landscape", "2024")
        date_start: Filter images uploaded after this date (YYYY-MM-DD)
        limit: Max number of results to return
    """
    with engine.connect() as conn:
        # 构建 SQL 查询
        sql = """
            SELECT DISTINCT i.iid, i.filename, i.location_str, i.shot_time
            FROM image i
            LEFT JOIN image_tags it ON i.iid = it.image_id
            LEFT JOIN tag t ON it.tag_id = t.tid
            WHERE 1=1
        """
        params = {}
        
        if keyword:
            sql += " AND (t.name LIKE :kw OR i.location_str LIKE :kw)"
            params['kw'] = f"%{keyword}%"
            
        if date_start:
            sql += " AND i.shot_time >= :date"
            params['date'] = date_start
            
        sql += " LIMIT :limit"
        params['limit'] = limit
        
        # 执行查询
        result = conn.execute(text(sql), params).fetchall()
        
        # 格式化返回结果给大模型
        images = []
        for row in result:
            images.append({
                "id": row[0],
                "filename": row[1],
                "location": row[2],
                "time": str(row[3]),
                # 构造本地访问 URL (假设 MCP 和网页在同一台机器)
                "url": f"http://localhost:5001/static/uploads/{row[1]}"
            })
            
        if not images:
            return "No images found matching criteria."
            
        return json.dumps(images, ensure_ascii=False, indent=2)

@mcp.tool()
def get_image_statistics():
    """Get total count of images and top tags."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM image")).scalar()
        tags = conn.execute(text("SELECT name, COUNT(*) as c FROM tag t JOIN image_tags it ON t.tid=it.tag_id GROUP BY t.tid ORDER BY c DESC LIMIT 5")).fetchall()
        
        tag_str = ", ".join([f"{t[0]}({t[1]})" for t in tags])
        return f"Total Images: {count}. Top Tags: {tag_str}"

if __name__ == "__main__":
    # 运行 MCP 服务器
    mcp.run()