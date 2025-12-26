from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app.models import News, Wiki
from crawler.crawler import crawl_all
from data_utils import get_wiki_preview, get_wiki_highlights, clean_news_summary
from datetime import datetime
import os
from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Elasticsearch와 AI 요약 임포트 (선택적)
try:
    from app.elasticsearch_client import create_indices, index_news, index_wiki, search_all, get_es_client
    from app.ai_summarizer import summarize_news
    ES_ENABLED = True
except Exception as e:
    print(f"[WARNING] Elasticsearch/AI disabled: {e}")
    ES_ENABLED = False

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="보안 뉴스 플랫폼")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 템플릿 설정
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Jinja2 커스텀 필터 등록
templates.env.filters['wiki_preview'] = lambda wiki, mode='short': get_wiki_preview(wiki, mode)
templates.env.filters['clean_summary'] = clean_news_summary

# 정적 파일 설정
static_path = os.path.join(BASE_DIR, "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Elasticsearch 인덱스 생성 (비동기 수행)"""
    if ES_ENABLED:
        import threading
        def init_es():
            try:
                create_indices()
                print("✅ Elasticsearch 인덱스 준비 완료")
            except Exception as e:
                print(f"⚠️ Elasticsearch 초기화 실패 (서버는 계속 실행됨): {e}")
        
        # 메인 루프를 방해하지 않도록 별도 스레드에서 실행
        threading.Thread(target=init_es, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """메인 페이지"""
    news_list = db.query(News).order_by(News.created_at.desc()).limit(50).all()
    wiki_list = db.query(Wiki).order_by(Wiki.created_at.desc()).all()
    
    stats = {
        "news_count": db.query(News).count(),
        "wiki_count": db.query(Wiki).count(),
        "es_enabled": ES_ENABLED
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
async def run_crawler(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """크롤링 실행"""
    try:
        count = crawl_all(db)
        
        # Elasticsearch에 인덱싱
        if ES_ENABLED:
            background_tasks.add_task(reindex_all_news)
        
        return {"success": True, "count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/news/{news_id}/summarize")
async def summarize_news_endpoint(news_id: int, db: Session = Depends(get_db)):
    """뉴스 AI 요약 생성"""
    if not ES_ENABLED:
        return {"success": False, "error": "AI 기능이 비활성화되어 있습니다"}
    
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        return {"success": False, "error": "뉴스를 찾을 수 없습니다"}
    
    if news.summary:
        return {"success": True, "summary": news.summary}
    
    # AI 요약 생성
    summary = summarize_news(news.title, news.url)
    if summary:
        news.summary = summary
        db.commit()
        
        # ES 업데이트
        if ES_ENABLED:
            index_news(news)
        
        return {"success": True, "summary": summary}
    else:
        return {"success": False, "error": "요약 생성 실패"}

@app.get("/api/search")
async def search(q: str, db: Session = Depends(get_db)):
    """통합 검색 (Elasticsearch 사용)"""
    if not q:
        return {"news": [], "wiki": []}
    
    if ES_ENABLED:
        try:
            results = search_all(q)
            return results
        except Exception as e:
            print(f"ES 검색 오류: {e}")
    
    # Fallback: SQLite 검색
    news = db.query(News).filter(
        (News.title.contains(q)) | (News.summary.contains(q))
    ).limit(20).all()
    
    wikis = db.query(Wiki).filter(
        (Wiki.title.contains(q)) | (Wiki.preview.contains(q)) | (Wiki.content.contains(q))
    ).limit(20).all()
    
    return {
        "news": [{"id": n.id, "title": n.title, "source": n.source, "summary": n.summary, "url": n.url} for n in news],
        "wiki": [{"id": w.id, "title": w.title, "category": w.category, "preview": w.preview} for w in wikis]
    }

@app.post("/api/wiki/add")
async def add_wiki(request: Request, db: Session = Depends(get_db)):
    """위키 추가"""
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
    
    # ES 인덱싱
    if ES_ENABLED:
        try:
            index_wiki(wiki)
        except Exception as e:
            print(f"ES 인덱싱 오류: {e}")
    
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

@app.get("/wiki/{wiki_id}", response_class=HTMLResponse)
async def wiki_detail(wiki_id: int, request: Request, db: Session = Depends(get_db)):
    """위키 상세 페이지"""
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id).first()
    if not wiki:
        return JSONResponse({"error": "위키를 찾을 수 없습니다"}, status_code=404)
    
    return templates.TemplateResponse("wiki_detail.html", {
        "request": request,
        "wiki": wiki
    })

def reindex_all_news():
    """모든 뉴스를 Elasticsearch에 재인덱싱"""
    if not ES_ENABLED:
        return
    
    db = next(get_db())
    try:
        news_list = db.query(News).all()
        for news in news_list:
            index_news(news)
        print(f"✅ {len(news_list)}개 뉴스 인덱싱 완료")
    except Exception as e:
        print(f"인덱싱 오류: {e}")
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """헬스 체크"""
    es_status = "disabled"
    if ES_ENABLED:
        try:
            es = get_es_client()
            if es.ping():
                es_status = "ok"
            else:
                es_status = "error"
        except:
            es_status = "error"
    
    return {
        "status": "ok",
        "elasticsearch": es_status
    }
