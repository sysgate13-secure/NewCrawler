import os, sys
# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from sqlalchemy import desc
from models import Wiki

def main():
    db = SessionLocal()
    w = db.query(Wiki).order_by(desc(Wiki.created_at)).limit(10).all()
    for i in w:
        print('TITLE:', i.title)
        print('CATEGORY:', i.category)
        print('TAGS:', i.tags)
        print('PREVIEW:', (i.preview or '')[:140])
        print('---')
    db.close()

if __name__ == '__main__':
    main()
