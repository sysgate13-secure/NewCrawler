from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import News
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
s = Session()

rows = s.query(News.source, News.id).all()
counts = {}
for src, _ in rows:
    counts[src] = counts.get(src, 0) + 1

print('총 항목 수 ->', len(rows))
for k, v in counts.items():
    print(f"{k}: {v}")

# 최근 추가된 항목 5개 출력
print('\n최근 5개 항목')
for n in s.query(News).order_by(News.id.desc()).limit(5).all():
    print(n.id, n.source, n.title[:70])

s.close()
