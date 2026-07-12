from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from kiro_platform.core.timezone_utils import get_beijing_time

from kiro_platform.core.database import get_db
from kiro_platform.api.v1.users import get_current_user
from kiro_platform.models.user import User
from kiro_platform.models.user_favorite import UserFavorite, DocumentLike
from kiro_platform.models.comment import Comment
from kiro_platform.models.notification import AuditLog
from kiro_knbase.models.document import Document
from kiro_knbase.models.category import Category, Tag

router = APIRouter(prefix="/statistics", tags=["统计分析"])


@router.get("/overview")
def get_overview_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库概览统计"""
    # 文档总数
    total_documents = db.query(Document).filter(Document.is_deleted == False).count()
    
    # 分类总数
    total_categories = db.query(Category).count()
    
    # 标签总数
    total_tags = db.query(Tag).count()
    
    # 用户总数
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # 本月新增文档
    this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    new_documents_this_month = db.query(Document).filter(
        Document.is_deleted == False,
        Document.created_at >= this_month
    ).count()
    
    # 总浏览量
    total_views = db.query(func.sum(Document.view_count)).scalar() or 0
    
    # 总点赞数
    total_likes = db.query(func.sum(Document.like_count)).scalar() or 0
    
    # 总评论数
    total_comments = db.query(Comment).count()
    
    return {
        "total_documents": total_documents,
        "total_categories": total_categories,
        "total_tags": total_tags,
        "total_users": total_users,
        "new_documents_this_month": new_documents_this_month,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments
    }


@router.get("/documents")
def get_document_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档统计数据"""
    # 按分类统计
    category_stats = db.query(
        Category.id,
        Category.name,
        func.count(Document.id).label('document_count')
    ).outerjoin(Document, Category.id == Document.category_id)\
     .filter(Document.is_deleted == False if Document.id else True)\
     .group_by(Category.id, Category.name)\
     .order_by(func.count(Document.id).desc())\
     .all()
    
    # 按权限统计
    permission_stats = db.query(
        Document.permission,
        func.count(Document.id).label('count')
    ).filter(Document.is_deleted == False)\
     .group_by(Document.permission)\
     .all()
    
    # 按状态统计
    status_stats = db.query(
        Document.status,
        func.count(Document.id).label('count')
    ).filter(Document.is_deleted == False)\
     .group_by(Document.status)\
     .all()
    
    # 最近7天新增文档趋势
    trend_data = []
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        count = db.query(Document).filter(
            Document.is_deleted == False,
            Document.created_at >= start_of_day,
            Document.created_at <= end_of_day
        ).count()
        
        trend_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "by_category": [{"category_id": c[0], "category_name": c[1], "count": c[2]} for c in category_stats],
        "by_permission": [{"permission": p[0], "count": p[1]} for p in permission_stats],
        "by_status": [{"status": s[0], "count": s[1]} for s in status_stats],
        "weekly_trend": trend_data
    }


@router.get("/users/activity")
def get_user_activity_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户活跃度统计"""
    # 活跃用户数（本月有操作的用户）
    this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    active_users_this_month = db.query(AuditLog.user_id).filter(
        AuditLog.created_at >= this_month
    ).distinct().count()
    
    # 按用户统计贡献
    user_contributions = db.query(
        Document.author_id,
        User.username,
        func.count(Document.id).label('document_count'),
        func.sum(Document.view_count).label('total_views'),
        func.sum(Document.like_count).label('total_likes')
    ).join(User, Document.author_id == User.id)\
     .filter(Document.is_deleted == False)\
     .group_by(Document.author_id, User.username)\
     .order_by(func.count(Document.id).desc())\
     .limit(20)\
     .all()
    
    # 今日活跃用户
    today = datetime.now().replace(hour=0, minute=0, second=0)
    today_active_users = db.query(AuditLog.user_id).filter(
        AuditLog.created_at >= today
    ).distinct().count()
    
    return {
        "active_users_this_month": active_users_this_month,
        "today_active_users": today_active_users,
        "top_contributors": [
            {
                "user_id": u[0],
                "username": u[1],
                "document_count": u[2],
                "total_views": u[3] or 0,
                "total_likes": u[4] or 0
            } for u in user_contributions
        ]
    }


@router.get("/documents/popular")
def get_popular_documents(
    limit: int = 10,
    period: str = "month",  # day, week, month, all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取热门文档排行榜"""
    query = db.query(Document).filter(Document.is_deleted == False)
    
    # 根据时间周期筛选
    if period == "day":
        since = datetime.now() - timedelta(days=1)
        query = query.filter(Document.updated_at >= since)
    elif period == "week":
        since = datetime.now() - timedelta(weeks=1)
        query = query.filter(Document.updated_at >= since)
    elif period == "month":
        since = datetime.now() - timedelta(weeks=4)
        query = query.filter(Document.updated_at >= since)
    
    # 按综合评分排序（浏览量*1 + 点赞*2 + 评论*3）
    query = query.order_by(
        (Document.view_count + Document.like_count * 2 + Document.comment_count * 3).desc()
    ).limit(limit)
    
    documents = query.all()
    
    results = []
    rank = 1
    for doc in documents:
        score = doc.view_count + doc.like_count * 2 + doc.comment_count * 3
        results.append({
            "rank": rank,
            "id": doc.id,
            "title": doc.title,
            "author_id": doc.author_id,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "comment_count": doc.comment_count,
            "score": score,
            "updated_at": doc.updated_at
        })
        rank += 1
    
    return results


@router.get("/users/contribution")
def get_user_contribution_statistics(
    user_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户贡献度统计"""
    if user_id:
        # 获取指定用户的贡献统计
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        doc_count = db.query(Document).filter(
            Document.author_id == user_id,
            Document.is_deleted == False
        ).count()
        
        total_views = db.query(func.sum(Document.view_count)).filter(
            Document.author_id == user_id,
            Document.is_deleted == False
        ).scalar() or 0
        
        total_likes = db.query(func.sum(Document.like_count)).filter(
            Document.author_id == user_id,
            Document.is_deleted == False
        ).scalar() or 0
        
        comment_count = db.query(Comment).filter(Comment.user_id == user_id).count()
        
        favorite_count = db.query(UserFavorite).filter(UserFavorite.user_id == user_id).count()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "document_count": doc_count,
            "total_views": total_views,
            "total_likes": total_likes,
            "comment_count": comment_count,
            "favorite_count": favorite_count,
            "contribution_score": doc_count * 10 + total_views + total_likes * 2 + comment_count * 3
        }
    else:
        # 获取贡献度排行榜
        contributions = db.query(
            User.id,
            User.username,
            func.count(Document.id).label('doc_count'),
            func.sum(Document.view_count).label('total_views'),
            func.sum(Document.like_count).label('total_likes')
        ).outerjoin(Document, User.id == Document.author_id)\
         .filter(User.is_active == True)\
         .group_by(User.id, User.username)\
         .order_by((func.count(Document.id) * 10 + func.sum(Document.view_count) + func.sum(Document.like_count) * 2).desc())\
         .limit(20)\
         .all()
        
        results = []
        rank = 1
        for c in contributions:
            score = (c[2] or 0) * 10 + (c[3] or 0) + (c[4] or 0) * 2
            results.append({
                "rank": rank,
                "user_id": c[0],
                "username": c[1],
                "document_count": c[2] or 0,
                "total_views": c[3] or 0,
                "total_likes": c[4] or 0,
                "contribution_score": score
            })
            rank += 1
        
        return results


@router.get("/export")
def export_statistics(
    type: str = "overview",  # overview, documents, users, popular
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出统计数据报表"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if type == "overview":
        stats = get_overview_statistics(db, current_user)
        writer.writerow(["指标", "数值"])
        for key, value in stats.items():
            writer.writerow([key, value])
        filename = "overview_statistics.csv"
    
    elif type == "documents":
        stats = get_document_statistics(db, current_user)
        output.write("=== 按分类统计 ===\n")
        writer.writerow(["分类ID", "分类名称", "文档数量"])
        for item in stats["by_category"]:
            writer.writerow([item["category_id"], item["category_name"], item["count"]])
        
        output.write("\n=== 按权限统计 ===\n")
        writer.writerow(["权限", "数量"])
        for item in stats["by_permission"]:
            writer.writerow([item["permission"], item["count"]])
        
        output.write("\n=== 按状态统计 ===\n")
        writer.writerow(["状态", "数量"])
        for item in stats["by_status"]:
            writer.writerow([item["status"], item["count"]])
        
        output.write("\n=== 近7天趋势 ===\n")
        writer.writerow(["日期", "新增文档数"])
        for item in stats["weekly_trend"]:
            writer.writerow([item["date"], item["count"]])
        
        filename = "document_statistics.csv"
    
    elif type == "users":
        stats = get_user_activity_statistics(db, current_user)
        output.write(f"本月活跃用户数,{stats['active_users_this_month']}\n")
        output.write(f"今日活跃用户数,{stats['today_active_users']}\n")
        
        output.write("\n=== 贡献排行榜 ===\n")
        writer.writerow(["排名", "用户ID", "用户名", "文档数", "总浏览量", "总点赞数"])
        for i, user in enumerate(stats["top_contributors"], 1):
            writer.writerow([
                i, user["user_id"], user["username"],
                user["document_count"], user["total_views"], user["total_likes"]
            ])
        
        filename = "user_statistics.csv"
    
    elif type == "popular":
        docs = get_popular_documents(limit=50, period="all", db=db, current_user=current_user)
        writer.writerow(["排名", "文档ID", "标题", "浏览量", "点赞数", "评论数", "综合评分"])
        for doc in docs:
            writer.writerow([
                doc["rank"], doc["id"], doc["title"],
                doc["view_count"], doc["like_count"], doc["comment_count"], doc["score"]
            ])
        
        filename = "popular_documents.csv"
    
    else:
        raise HTTPException(status_code=400, detail="无效的导出类型")
    
    output.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "text/csv; charset=utf-8"
    }
    
    return StreamingResponse(output, headers=headers)