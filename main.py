from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import News, Wiki
from crawler import crawl_all
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

@app.post("/api/crawl")
async def run_crawler(db: Session = Depends(get_db)):
    """크롤링 실행"""
    count = crawl_all(db)
    return {"success": True, "count": count}

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
