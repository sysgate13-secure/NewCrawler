from app.database import SessionLocal
from app.models import News, Wiki

def cleanup_chinese_chars():
    db = SessionLocal()
    try:
        # 뉴스 요약 정리
        news_items = db.query(News).filter(
            (News.summary.like('%蜘蛛%')) | 
            (News.summary.like('%歌曲%')) | 
            (News.summary.like('%勒%'))
        ).all()
        
        for item in news_items:
            print(f"Cleaning News ID {item.id}...")
            item.summary = item.summary.replace('蜘蛛', '크롤러')
            item.summary = item.summary.replace('歌曲', '곡/노래')
            item.summary = item.summary.replace('勒', '랜섬')
        
        # 위키 콘텐츠 정리
        wiki_items = db.query(Wiki).filter(
            (Wiki.content.like('%蜘蛛%')) | 
            (Wiki.content.like('%歌曲%')) | 
            (Wiki.content.like('%勒%'))
        ).all()
        
        for item in wiki_items:
            print(f"Cleaning Wiki ID {item.id}...")
            item.content = item.content.replace('蜘蛛', '크롤러')
            item.content = item.content.replace('歌曲', '곡/노래')
            item.content = item.content.replace('勒', '랜섬')
            if item.preview:
                item.preview = item.preview.replace('蜘蛛', '크롤러')
                item.preview = item.preview.replace('歌曲', '곡/노래')
                item.preview = item.preview.replace('勒', '랜섬')

        db.commit()
        print(f"Cleanup finished. Modified {len(news_items)} news items and {len(wiki_items)} wiki items.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_chinese_chars()
