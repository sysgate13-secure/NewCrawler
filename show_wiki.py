from database import SessionLocal
from models import Wiki

db = SessionLocal()
wikis = db.query(Wiki).all()
print(f"wiki count -> {len(wikis)}")
for w in wikis:
    print(f"{w.id} | {w.title[:40]} | {w.category}")
db.close()
