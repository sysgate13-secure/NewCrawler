from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import News
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
s = Session()

last_10 = s.query(News).order_by(News.id.desc()).limit(10).all()
for n in last_10:
    print(f"[{n.id}] {n.title[:50]}")
    print(f"   Source: {n.source}")
    print(f"   Summary: {n.summary}")
    print("-" * 50)
s.close()
