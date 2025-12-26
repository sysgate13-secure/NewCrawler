from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Wiki
from app.database import SQLALCHEMY_DATABASE_URL
from app.ai_summarizer import generate_wiki_content
import time

# DB 연결
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

def regenerate_wiki():
    """기존 위키 내용들을 새로운 형식(기술 설명, 공격 방식, 방어 전략)으로 재생성"""
    print("=== 위키 콘텐츠 재생성 시작 ===")
    
    # 자동으로 생성된(auto) 위키 항목들 조회
    wiki_items = db.query(Wiki).filter(Wiki.type == "auto").all()
    
    print(f"대상 항목 수: {len(wiki_items)}")
    
    updated = 0
    for item in wiki_items:
        try:
            print(f"처리 중: {item.title[:50]}...")
            
            # 새로운 형식으로 콘텐츠 생성
            new_content = generate_wiki_content(item.title, item.category)
            
            if new_content:
                item.content = new_content
                db.commit()
                updated += 1
                print(f"   완료 (길이: {len(new_content)})")
            else:
                print("   실패: AI 응답 없음")
                
            time.sleep(1.5) # 모델 부하 조절 및 상세 생성을 위해 약간 더 대기
            
        except Exception as e:
            print(f"   오류: {e}")
            db.rollback()

    print(f"=== 위키 재생성 완료: {updated}개 업데이트됨 ===")

if __name__ == "__main__":
    try:
        regenerate_wiki()
    finally:
        db.close()
