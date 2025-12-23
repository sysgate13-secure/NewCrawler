"""
크롤러 테스트 스크립트
실제로 크롤링이 작동하는지 확인
"""
from database import SessionLocal
from crawler import crawl_all

if __name__ == "__main__":
    print("=" * 50)
    print("보안 뉴스 크롤러 테스트")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        count = crawl_all(db)
        print(f"\n총 {count}개의 뉴스가 수집되었습니다.")
        
        if count == 0:
            print("\n⚠️ 수집된 뉴스가 없습니다.")
            print("원인:")
            print("1. 인터넷 연결 확인")
            print("2. 대상 사이트의 HTML 구조 변경 가능성")
            print("3. 크롤러 차단 가능성")
        else:
            print(f"\n✅ 크롤링 성공!")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        db.close()
