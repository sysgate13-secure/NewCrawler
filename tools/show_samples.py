from app.database import SessionLocal
from app.models import News, Wiki
from sqlalchemy import desc

def show():
    db = SessionLocal()
    print('--- 최근 뉴스 (최대5) ---')
    news = db.query(News).order_by(desc(News.created_at)).limit(5).all()
    for n in news:
        print(f"- [{n.category}] {n.title} ({n.source}) - {n.url}")

    print('\n--- 최근 위키 (최대5) ---')
    wikis = db.query(Wiki).order_by(desc(Wiki.created_at)).limit(5).all()
    for w in wikis:
        print(f"- [{w.category}] {w.title} (type={w.type})")
        print('  preview:', (w.preview or '')[:140])
        print('  content-start:', (w.content or '')[:200].replace('\n',' '))
        print()
    db.close()

if __name__ == '__main__':
    show()
