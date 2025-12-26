from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import News
from app.database import SQLALCHEMY_DATABASE_URL
from app.ai_summarizer import summarize_news
import time

# DB 연결
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

def batch_summarize():
    """요약이 없거나 부족한 뉴스들을 AI로 일괄 요약"""
    print("=== 일괄 AI 요약 시작 ===")
    
    # 요약이 비어있거나 너무 짧은 항목들 조회 (AI 요약이 아닌 경우)
    # 여기서는 간단히 제목만 있거나 요약이 50자 미만인 항목들을 대상으로 함
    news_items = db.query(News).filter((News.summary == "") | (News.summary == None)).all()
    
    print(f"대상 항목 수: {len(news_items)}")
    
    updated = 0
    for item in news_items:
        try:
            print(f"요약 중: {item.title[:50]}...")
            # 본문이 없으면 제목으로라도 시도
            new_summary = summarize_news(item.title, item.summary)
            
            if new_summary:
                item.summary = new_summary
                db.commit()
                updated += 1
                print(f"   완료: {new_summary[:100]}...")
            else:
                print("   실패: AI 응답 없음")
                
            time.sleep(1) # 모델 부하 조절
            
        except Exception as e:
            print(f"   오류: {e}")
            db.rollback()

    print(f"=== 일괄 요약 완료: {updated}개 업데이트됨 ===")

if __name__ == "__main__":
    try:
        batch_summarize()
    finally:
        db.close()
