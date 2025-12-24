from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import News, Wiki, CrawlLog
from crawler import crawl_all
from datetime import datetime
import os

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="보안 뉴스 플랫폼")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 설정 (있으면)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """메인 페이지"""
    news_list = db.query(News).order_by(News.created_at.desc()).limit(50).all()
    wiki_list = db.query(Wiki).order_by(Wiki.created_at.desc()).all()
    
    stats = {
        "news_count": db.query(News).count(),
        "wiki_count": db.query(Wiki).count()
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_list": news_list,
        "wiki_list": wiki_list,
        "stats": stats
    })

@app.get("/api/news")
async def get_news(db: Session = Depends(get_db)):
    """뉴스 API"""
    news = db.query(News).order_by(News.created_at.desc()).limit(50).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "source": n.source,
            "date": n.date,
            "summary": n.summary,
            "category": n.category,
            "url": n.url
        }
        for n in news
    ]

@app.get("/api/news/search")
async def search_news(q: str = "", category: str = "", db: Session = Depends(get_db)):
    """뉴스 검색 (제목, 요약, 카테고리 기준)"""
    query = db.query(News)
    
    if q:
        query = query.filter(
            (News.title.contains(q)) | (News.summary.contains(q))
        )
    
    if category:
        query = query.filter(News.category == category)
    
    news = query.order_by(News.created_at.desc()).limit(50).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "source": n.source,
            "date": n.date,
            "summary": n.summary,
            "category": n.category,
            "url": n.url
        }
        for n in news
    ]

@app.get("/api/wiki")
async def get_wiki(db: Session = Depends(get_db)):
    """위키 API"""
    wikis = db.query(Wiki).order_by(Wiki.created_at.desc()).all()
    return [
        {
            "id": w.id,
            "title": w.title,
            "category": w.category,
            "preview": w.preview,
            "type": w.type
        }
        for w in wikis
    ]

@app.get("/api/wiki/search")
async def search_wiki(q: str = "", category: str = "", db: Session = Depends(get_db)):
    """위키 검색 (제목, 카테고리 기준)"""
    query = db.query(Wiki)
    
    if q:
        query = query.filter(
            (Wiki.title.contains(q)) | (Wiki.preview.contains(q))
        )
    
    if category:
        query = query.filter(Wiki.category == category)
    
    wikis = query.order_by(Wiki.created_at.desc()).all()
    return [
        {
            "id": w.id,
            "title": w.title,
            "category": w.category,
            "preview": w.preview,
            "type": w.type
        }
        for w in wikis
    ]

@app.post("/api/crawl")
async def run_crawler(db: Session = Depends(get_db)):
    """크롤링 실행 + 로그 기록"""
    log = CrawlLog(status="running", message="크롤링 시작")
    db.add(log)
    db.commit()
    
    try:
        count = crawl_all(db)
        log.status = "success"
        log.count = count
        log.completed_at = datetime.now()
        log.message = f"크롤링 완료: {count}개 추가"
        db.commit()
        return {"success": True, "count": count}
    except Exception as e:
        log.status = "failed"
        log.completed_at = datetime.now()
        log.message = str(e)
        db.commit()
        return {"success": False, "error": str(e)}

@app.get("/api/crawl/status")
async def get_crawl_status(db: Session = Depends(get_db)):
    """최근 크롤링 상태 조회"""
    recent = db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).first()
    if not recent:
        return {"status": "not_started", "message": "크롤링 이력 없음"}
    
    return {
        "status": recent.status,
        "message": recent.message,
        "count": recent.count,
        "started_at": recent.started_at.isoformat(),
        "completed_at": recent.completed_at.isoformat() if recent.completed_at else None
    }

@app.get("/api/crawl/history")
async def get_crawl_history(limit: int = 10, db: Session = Depends(get_db)):
    """크롤링 이력 조회"""
    logs = db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "status": log.status,
            "count": log.count,
            "message": log.message,
            "started_at": log.started_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None
        }
        for log in logs
    ]

@app.get("/api/stats/categories")
async def get_category_stats(db: Session = Depends(get_db)):
    """카테고리별 통계"""
    from sqlalchemy import func
    
    news_by_cat = db.query(News.category, func.count(News.id)).group_by(News.category).all()
    wiki_by_cat = db.query(Wiki.category, func.count(Wiki.id)).group_by(Wiki.category).all()
    
    return {
        "news_categories": {cat: count for cat, count in news_by_cat},
        "wiki_categories": {cat: count for cat, count in wiki_by_cat}
    }

@app.post("/api/wiki/add")
async def add_wiki(
    title: str,
    category: str,
    preview: str,
    content: str = "",
    type: str = "",
    db: Session = Depends(get_db)
):
    """위키 추가"""
    wiki = Wiki(
        title=title,
        category=category,
        preview=preview,
        content=content,
        type=type
    )
    db.add(wiki)
    db.commit()
    return {"success": True, "id": wiki.id}
@app.post("/api/wiki/add")
async def add_wiki(
    request: Request,
    db: Session = Depends(get_db)
):
    """위키 추가 (폼 데이터)"""
    form = await request.form()
    
    wiki = Wiki(
        title=form.get("title"),
        category=form.get("category"),
        preview=form.get("preview"),
        content=form.get("content", ""),
        type=form.get("type", "")
    )
    db.add(wiki)
    db.commit()
    
    return JSONResponse({
        "success": True, 
        "id": wiki.id,
        "message": "위키가 추가되었습니다."
    })

@app.get("/wiki/manage", response_class=HTMLResponse)
async def wiki_manage(request: Request, db: Session = Depends(get_db)):
    """위키 관리 페이지"""
    wikis = db.query(Wiki).order_by(Wiki.created_at.desc()).all()
    return templates.TemplateResponse("wiki_manage.html", {
        "request": request,
        "wikis": wikis
    })
