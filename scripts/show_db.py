from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import News, Wiki
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

s = Session()
print('news count ->', s.query(News).count())
for n in s.query(News).all():
    print(n.id, n.title[:40], n.url)
s.close()
