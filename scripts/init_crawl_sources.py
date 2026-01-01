"""
기본 크롤링 소스를 DB에 추가하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import CrawlSource

def init_default_sources():
    """기본 크롤링 소스들을 DB에 추가"""
    db = SessionLocal()
    
    try:
        # 기존에 있는지 확인
        existing_count = db.query(CrawlSource).count()
        if existing_count > 0:
            print(f"ℹ️ 이미 {existing_count}개의 소스가 등록되어 있습니다.")
            choice = input("기존 데이터를 유지하고 추가하시겠습니까? (y/n): ")
            if choice.lower() != 'y':
                print("취소되었습니다.")
                return
        
        default_sources = [
            {
                "name": "ZDNet Korea",
                "url": "https://www.zdnet.co.kr/news/security/",
                "country": "kr",
                "description": "ZDNet 코리아의 보안 뉴스 섹션",
                "selector_config": '{"title_selector": ".card-item h2", "summary_selector": ".desc"}'
            },
            {
                "name": "CyberScoop",
                "url": "https://cyberscoop.com/news/",
                "country": "en",
                "description": "미국의 사이버 보안 전문 뉴스",
                "selector_config": '{"title_selector": ".post-item__title-link", "summary_selector": ".post-item__excerpt"}'
            },
            {
                "name": "HelpNetSecurity",
                "url": "https://www.helpnetsecurity.com/view/news/",
                "country": "en",
                "description": "네트워크 보안 뉴스 및 정보",
                "selector_config": '{"title_selector": ".card-title a"}'
            },
        ]
        
        added = 0
        for source_data in default_sources:
            # 중복 체크
            existing = db.query(CrawlSource).filter(
                CrawlSource.url == source_data["url"]
            ).first()
            
            if not existing:
                source = CrawlSource(**source_data, is_active=True)
                db.add(source)
                added += 1
                print(f"✅ {source_data['name']} 추가됨")
            else:
                print(f"ℹ️ {source_data['name']} 이미 존재함")
        
        db.commit()
        print(f"\n✨ 총 {added}개의 새 소스가 추가되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_default_sources()
