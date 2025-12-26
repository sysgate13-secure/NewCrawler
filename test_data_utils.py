"""
서버 실행 전 빠른 테스트
"""
import sys
sys.path.insert(0, 'C:\\Users\\김민재\\Desktop\\security-news-platform')

from database import SessionLocal
from models import Wiki
from data_utils import get_wiki_preview, get_wiki_highlights

try:
    db = SessionLocal()
    
    wikis = db.query(Wiki).limit(3).all()
    
    print("=" * 70)
    print("위키 데이터 정제 결과")
    print("=" * 70)
    
    for wiki in wikis:
        print(f"\n[제목] {wiki.title}")
        print("-" * 70)
        
        print("\n짧게 (메인 페이지용):")
        print(get_wiki_preview(wiki, mode='short'))
        
        print("\n중간 (검색 결과용):")
        print(get_wiki_preview(wiki, mode='medium'))
        
        highlights = get_wiki_highlights(wiki)
        print(f"\n핵심 포인트 {len(highlights['key_points'])}개:")
        for i, point in enumerate(highlights['key_points'], 1):
            print(f"  {i}. {point}")
        
        print("\n" + "=" * 70)
    
    db.close()
    print("\n테스트 성공!")
    
except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()
