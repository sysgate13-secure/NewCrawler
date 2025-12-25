import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import News, Wiki
from crawler.crawler import determine_category, extract_keywords


def main():
    db = SessionLocal()
    try:
        news_rows = db.query(News).all()
    except Exception as e:
        print('Failed to read News:', e)
        return

    n_updated = 0
    for r in news_rows:
        text = f"{r.title} {r.summary or ''}"
        new_cat = determine_category(text)
        if (r.category or '') != new_cat:
            r.category = new_cat
            n_updated += 1

    try:
        db.commit()
    except Exception as e:
        print('Failed to commit News updates:', e)

    try:
        wiki_rows = db.query(Wiki).all()
    except Exception as e:
        print('Failed to read Wiki:', e)
        wiki_rows = []

    w_updated = 0
    for w in wiki_rows:
        text = f"{w.title} {(w.preview or '')} {(w.content or '')}"
        new_cat = determine_category(text)
        new_tags = ','.join(extract_keywords((w.preview or '') + ' ' + (w.content or ''), top_n=6))
        changed = False
        if (w.category or '') != new_cat:
            w.category = new_cat
            changed = True
        if (w.tags or '') != new_tags:
            w.tags = new_tags
            changed = True
        if changed:
            w_updated += 1

    try:
        db.commit()
    except Exception as e:
        print('Failed to commit Wiki updates:', e)

    db.close()

    print(f"Reclassification complete. News updated: {n_updated}, Wiki updated: {w_updated}")


if __name__ == '__main__':
    main()
