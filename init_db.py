from database import SessionLocal, engine, Base
from models import News, Wiki
from datetime import datetime

# DB 초기화
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# SQLite: 위키 테이블에 `tags` 컬럼이 없으면 추가
from sqlalchemy import text

with engine.connect() as conn:
    cols = conn.execute(text("PRAGMA table_info('wiki')")).fetchall()
    col_names = [c[1] for c in cols]
    if 'tags' not in col_names:
        try:
            conn.execute(text("ALTER TABLE wiki ADD COLUMN tags TEXT"))
            print('✅ wiki.tags 컬럼 추가됨')
        except Exception as e:
            print('wiki.tags 컬럼 추가 실패:', e)

# 샘플 뉴스 데이터
sample_news = [
    {
        "title": "새로운 랜섬웨어 'BlackCat' 변종 발견, 기업 대상 공격 증가",
        "source": "보안뉴스",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": "최근 발견된 BlackCat 랜섬웨어의 새로운 변종이 국내외 기업들을 대상으로 공격을 가하고 있어 주의가 필요합니다.",
        "category": "malware",
        "url": "#"
    },
    {
        "title": "Zero Trust 보안 모델 도입 기업 70% 증가",
        "source": "보안뉴스",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": "2025년 들어 Zero Trust 보안 모델을 도입한 기업이 전년 대비 70% 증가했다고 보고되었습니다.",
        "category": "trend",
        "url": "#"
    }
]

# 샘플 위키 데이터
sample_wiki = [
    {
        "title": "SQL 인젝션 공격과 방어",
        "category": "웹 보안",
        "preview": "SQL 인젝션은 웹 애플리케이션의 데이터베이스 쿼리에 악의적인 SQL 코드를 삽입하는 공격 기법입니다.",
        "content": "",
        "type": "web"
    },
    {
        "title": "Zero Trust 네트워크 아키텍처",
        "category": "네트워크",
        "preview": "'절대 신뢰하지 말고 항상 검증하라'는 원칙에 기반한 보안 모델입니다.",
        "content": "",
        "type": "network"
    }
]

# 데이터 추가
for news_data in sample_news:
    news = News(**news_data)
    db.add(news)

for wiki_data in sample_wiki:
    wiki = Wiki(**wiki_data)
    db.add(wiki)

db.commit()
print("✅ 샘플 데이터 추가 완료")
db.close()
