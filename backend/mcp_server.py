# mcp_server.py
from mcp.server.fastmcp import FastMCP
import pymysql
import os
from dotenv import load_dotenv

load_dotenv() 

# 创建 MCP 服务，名字叫 "PhotoSys"
mcp = FastMCP("PhotoSys")

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', '3306')) # pymysql 需要整数类型的端口

# 数据库配置 (请修改为你的实际配置)
DB_CONFIG = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "port": DB_PORT,
    "cursorclass": pymysql.cursors.DictCursor
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

@mcp.tool()
def search_images(keywords: str = None, location: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    根据条件搜索图片数据库。
    
    Args:
        keywords: 搜索关键词，如 '猫', '风景', '红色'
        location: 地点字符串，如 '杭州'
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
    """
    sql = """
    SELECT 
        i.iid, i.filename, i.url, i.thumb_url, i.location_str, i.shot_time,
        GROUP_CONCAT(t.name) as tags
    FROM image i
    LEFT JOIN image_tags it ON i.iid = it.image_id
    LEFT JOIN tag t ON it.tag_id = t.tid
    WHERE 1=1
    """
    params = []

    if keywords:
        sql += " AND (i.filename LIKE %s OR t.name LIKE %s)"
        params.extend([f"%{keywords}%", f"%{keywords}%"])
    
    if location:
        sql += " AND i.location_str LIKE %s"
        params.append(f"%{location}%")

    if start_date:
        sql += " AND i.shot_time >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND i.shot_time <= %s"
        params.append(end_date)

    sql += " GROUP BY i.iid ORDER BY i.shot_time DESC LIMIT 20"

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
        conn.close()
        
        # 将结果处理成更轻量的 JSON 字符串返回
        images = []
        for row in results:
            images.append({
                "id": row['iid'],
                "url": row['url'],
                "thumb": row['thumb_url'] or row['url'], # 优先用缩略图
                "name": row['filename'],
                "location": row['location_str'],
                "date": str(row['shot_time'])
            })
            
        import json
        return json.dumps(images, ensure_ascii=False)
        
    except Exception as e:
        return f"查询出错: {str(e)}"

if __name__ == "__main__":
    # 使用 stdio 模式运行，这是 MCP 的标准运行方式
    mcp.run(transport='stdio')