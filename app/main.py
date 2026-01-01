import bleach
from fastapi import FastAPI, Depends, Request, BackgroundTasks, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app.models import News, Wiki, CrawlSource
from crawler.crawler import crawl_all
from data_utils import get_wiki_preview, get_wiki_highlights, clean_news_summary
from datetime import datetime
import os
import math


# Elasticsearch와 AI 요약 임포트 (선택적)
try:
    from app.elasticsearch_client import create_indices, index_news, index_wiki, search_all, get_es_client, search_news, search_wiki
    from app.ai_summarizer import summarize_news
    # 기본적으로 켜져 있으나 USE_ELASTICSEARCH=false 설정 시 비활성화
    ES_ENABLED = os.getenv("USE_ELASTICSEARCH", "true").lower() == "true"
except Exception as e:
    if os.getenv("USE_ELASTICSEARCH", "true").lower() == "true":
        print(f"[WARNING] Elasticsearch/AI components load failed: {e}")
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
templates.env.filters['format_date'] = lambda dt: dt.strftime('%Y-%m-%d') if hasattr(dt, 'strftime') else str(dt)[:10] if dt else 'N/A'

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
                print(f"ℹ️ Elasticsearch가 실행 중이지 않아 검색 엔진 기능이 비활성화되었습니다. (SQLite는 정상 작동함)")
        
        # 메인 루프를 방해하지 않도록 별도 스레드에서 실행
        threading.Thread(target=init_es, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20
):
    """메인 페이지"""
    news_query = db.query(News).order_by(News.created_at.desc())
    
    total_news = news_query.count()
    total_pages = math.ceil(total_news / limit) if total_news > 0 else 1
    
    offset = (page - 1) * limit
    news_list = news_query.offset(offset).limit(limit).all()
    
    wiki_list = db.query(Wiki).order_by(Wiki.created_at.desc()).all()
    
    stats = {
        "news_count": total_news,
        "wiki_count": db.query(Wiki).count(),
        "es_enabled": ES_ENABLED
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_list": news_list,
        "wiki_list": wiki_list,
        "stats": stats,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_items": total_news
        }
    })

@app.get("/api/news")
async def get_news(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20
):
    """뉴스 API"""
    news_query = db.query(News).order_by(News.created_at.desc())
    
    total_news = news_query.count()
    total_pages = math.ceil(total_news / limit) if total_news > 0 else 1
    
    offset = (page - 1) * limit
    news = news_query.offset(offset).limit(limit).all()

    news_data = [
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
    
    return {
        "news": news_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_items": total_news
        }
    }

@app.delete("/api/news/{news_id}", status_code=200)
async def delete_news_item(news_id: int, db: Session = Depends(get_db)):
    """뉴스 기사 삭제"""
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
    
    db.delete(news_item)
    db.commit()
    
    # ES에서도 삭제 (필요 시)
    if ES_ENABLED:
        try:
            get_es_client().delete(index="news", id=news_id, ignore=[404])
        except Exception as e:
            print(f"ES 뉴스 삭제 오류: {e}")

    return {"message": "뉴스가 성공적으로 삭제되었습니다."}

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
        return {"success": False, "error": "str(e)"}

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
async def search(
    q: str = "",
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    category: str = "",
    index: str = "all"  # 'news', 'wiki', or 'all'
):
    """통합 검색 (Elasticsearch 사용)"""
    if not ES_ENABLED:
        # Fallback to SQLite if ES is disabled
        pass  # The original SQLite fallback logic will be executed at the end

    else:
        try:
            # 뉴스만 검색
            if index == 'news':
                es_results = search_news(q, page=page, limit=limit, category=category)
                total_pages = math.ceil(es_results["total"] / limit) if es_results["total"] > 0 else 1
                return {
                    "news": es_results["results"],
                    "wiki": [],
                    "pagination": {
                        "page": page, "limit": limit, "total_pages": total_pages, "total_items": es_results["total"]
                    }
                }

            # 위키만 검색
            elif index == 'wiki':
                es_results = search_wiki(q, page=page, limit=limit, category=category)
                total_pages = math.ceil(es_results["total"] / limit) if es_results["total"] > 0 else 1
                return {
                    "news": [],
                    "wiki": es_results["results"],
                    "pagination": {
                        "page": page, "limit": limit, "total_pages": total_pages, "total_items": es_results["total"]
                    }
                }

            # 기본: 전체 검색
            else: # index == 'all'
                es_results = search_all(q, page=page, limit=limit, category=category)
                total_news = es_results["news_total"]
                total_pages = math.ceil(total_news / limit) if total_news > 0 else 1
                
                return {
                    "news": es_results["news"],
                    "wiki": es_results["wiki"],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total_pages": total_pages,
                        "total_items": total_news
                    }
                }
        except Exception:
            pass  # Fallback to SQLite

    # Fallback: SQLite 검색
    if index == 'news' or index == 'all':
        news_query = db.query(News)
        if q:
            news_query = news_query.filter(
                (News.title.contains(q)) | (News.summary.contains(q))
            )
        if category:
            news_query = news_query.filter(News.category == category)
            
        total_news = news_query.count()
        total_pages = math.ceil(total_news / limit) if total_news > 0 else 1
        offset = (page - 1) * limit
        
        news = news_query.order_by(News.created_at.desc()).offset(offset).limit(limit).all()
        news_data = [{
            "id": n.id, "title": n.title, "source": n.source, "summary": n.summary, 
            "url": n.url, "category": n.category, "date": n.date
        } for n in news]
    else:
        news_data = []
        total_news = 0
        total_pages = 1
    
    # 위키 검색 (index='wiki' 또는 'all'이고 검색어가 있을 때만)
    if (index == 'wiki' or index == 'all') and q:
        wikis = db.query(Wiki).filter(
            (Wiki.title.contains(q)) | (Wiki.preview.contains(q)) | (Wiki.content.contains(q))
        ).limit(20).all()
        wiki_data = [{"id": w.id, "title": w.title, "category": w.category, "preview": w.preview, "tags": w.tags} for w in wikis]
    else:
        wiki_data = []
    
    return {
        "news": news_data,
        "wiki": wiki_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_items": total_news
        }
    }

@app.post("/api/wiki/add")
async def add_wiki(request: Request, db: Session = Depends(get_db)):
    """위키 추가"""
    form = await request.form()
    
    wiki = Wiki(
        title=bleach.clean(form.get("title")),
        category=form.get("category"),
        preview=bleach.clean(form.get("preview")),
        content=bleach.clean(form.get("content", ""), tags=['p', 'a', 'strong', 'em', 'ul', 'li', 'h1', 'h2', 'h3']),
        type=form.get("type", "")
    )
    db.add(wiki)
    db.commit()
    
    # ES 인덱싱
    if ES_ENABLED:
        try:
            index_wiki(wiki)
        except Exception as e:
            pass  # ES 비활성화 시 조용히 무시
    
    return JSONResponse({
        "success": True, 
        "id": wiki.id,
        "message": "위키가 추가되었습니다."
    })

@app.get("/wiki/{wiki_id}/edit", response_class=HTMLResponse)
async def wiki_edit_form(wiki_id: int, request: Request, db: Session = Depends(get_db)):
    """위키 수정 페이지"""
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id).first()
    if not wiki:
        return HTMLResponse("위키를 찾을 수 없습니다", status_code=404)
    return templates.TemplateResponse("wiki_manage.html", {
        "request": request,
        "wiki_to_edit": wiki,
        "wikis": [] # 목록은 안 보여줘도 됨
    })

@app.post("/api/wiki/{wiki_id}/edit")
async def wiki_edit(wiki_id: int, request: Request, db: Session = Depends(get_db)):
    """위키 수정 처리"""
    form = await request.form()
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id).first()
    if not wiki:
        return JSONResponse({"success": False, "error": "위키를 찾을 수 없습니다"})
    
    wiki.title = bleach.clean(form.get("title"))
    wiki.category = form.get("category")
    wiki.preview = bleach.clean(form.get("preview"))
    wiki.content = bleach.clean(form.get("content", ""), tags=['p', 'a', 'strong', 'em', 'ul', 'li', 'h1', 'h2', 'h3'])
    wiki.type = "manual" # 수동 수정됨
    
    db.commit()
    
    if ES_ENABLED:
        try:
            index_wiki(wiki)
        except Exception as e:
            pass  # ES 비활성화 시 조용히 무시
            
    return JSONResponse({"success": True, "message": "수정되었습니다."})

def delete_es_wiki_background(wiki_id: int):
    """백그라운드에서 Elasticsearch의 위키 문서를 삭제합니다."""
    try:
        get_es_client().delete(index="wiki", id=wiki_id, ignore=[404])
        print(f"✅ ES에서 위키 ID {wiki_id}가 삭제되었습니다.")
    except Exception as e:
        print(f"❌ ES 위키 삭제 오류 (ID: {wiki_id}): {e}")

@app.post("/api/wiki/{wiki_id}/delete")
async def wiki_delete(
    wiki_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """위키 삭제 처리 (ES 삭제는 백그라운드 수행)"""
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id).first()
    if not wiki:
        return JSONResponse({"success": False, "error": "위키를 찾을 수 없습니다"})
    
    # DB에서 즉시 삭제
    db.delete(wiki)
    db.commit()
    
    # ES 삭제는 백그라운드 작업으로 위임하여 응답 속도 개선
    if ES_ENABLED:
        background_tasks.add_task(delete_es_wiki_background, wiki_id)
    
    return JSONResponse({"success": True, "message": "삭제되었습니다."})

@app.get("/wiki/manage", response_class=HTMLResponse)
async def wiki_manage(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10
):
    """위키 관리 페이지"""
    wiki_query = db.query(Wiki).order_by(Wiki.created_at.desc())
    
    total_wikis = wiki_query.count()
    total_pages = math.ceil(total_wikis / limit) if total_wikis > 0 else 1
    
    offset = (page - 1) * limit
    wikis = wiki_query.offset(offset).limit(limit).all()
    
    return templates.TemplateResponse("wiki_manage.html", {
        "request": request,
        "wikis": wikis,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_items": total_wikis
        }
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
@app.get("/api/stats/sources")
async def get_source_stats(db: Session = Depends(get_db)):
    """소스별 뉴스 통계"""
    from sqlalchemy import func
    
    stats = db.query(
        News.source,
        func.count(News.id).label('count')
    ).group_by(News.source).order_by(func.count(News.id).desc()).all()
    
    return [{"source": s.source, "count": s.count} for s in stats]

@app.get("/api/stats/categories")
async def get_category_stats(db: Session = Depends(get_db)):
    """카테고리별 뉴스 통계"""
    from sqlalchemy import func
    
    stats = db.query(
        News.category,
        func.count(News.id).label('count')
    ).group_by(News.category).order_by(func.count(News.id).desc()).all()
    
    category_labels = {
        'malware': '악성코드',
        'vulnerability': '취약점',
        'network': '네트워크',
        'web': '웹 보안',
        'crypto': '암호학',
        'trend': '기타'
    }
    
    return [
        {
            "category": s.category,
            "label": category_labels.get(s.category, s.category),
            "count": s.count
        } 
        for s in stats
    ]


# 크롤링 소스 관리 API
@app.get("/sources/manage", response_class=HTMLResponse)
async def sources_manage(request: Request, db: Session = Depends(get_db)):
    """크롤링 소스 관리 페이지"""
    sources = db.query(CrawlSource).order_by(CrawlSource.created_at.desc()).all()
    return templates.TemplateResponse("sources_manage.html", {
        "request": request,
        "sources": sources
    })

@app.get("/api/sources")
async def get_sources(db: Session = Depends(get_db)):
    """크롤링 소스 목록"""
    sources = db.query(CrawlSource).order_by(CrawlSource.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "country": s.country,
            "description": s.description,
            "is_active": s.is_active,
            "created_at": s.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for s in sources
    ]

@app.post("/api/sources/add")
async def add_source(request: Request, db: Session = Depends(get_db)):
    """크롤링 소스 추가"""
    form = await request.form()
    
    source = CrawlSource(
        name=bleach.clean(form.get("name")),
        url=form.get("url"),
        country=form.get("country"),
        description=bleach.clean(form.get("description", "")),
        selector_config=form.get("selector_config", "{}"),
        is_active=True
    )
    db.add(source)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "id": source.id,
        "message": "크롤링 소스가 추가되었습니다."
    })

@app.post("/api/sources/{source_id}/toggle")
async def toggle_source(source_id: int, db: Session = Depends(get_db)):
    """크롤링 소스 활성화/비활성화"""
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        return JSONResponse({"success": False, "error": "소스를 찾을 수 없습니다"})
    
    source.is_active = not source.is_active
    db.commit()
    
    return JSONResponse({
        "success": True,
        "is_active": source.is_active,
        "message": f"소스가 {'활성화' if source.is_active else '비활성화'}되었습니다."
    })

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """크롤링 소스 삭제"""
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="소스를 찾을 수 없습니다.")
    
    db.delete(source)
    db.commit()
    
    return {"message": "소스가 성공적으로 삭제되었습니다."}
