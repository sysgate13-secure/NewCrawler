import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from models import News
import time

def crawl_boannews(db: Session):
    """보안뉴스 크롤링"""
    url = "https://www.boannews.com/media/t_list.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        news_items = soup.select('div.news_list')
        
        for item in news_items[:15]:
            try:
                # a 태그에서 링크 추출
                link_tag = item.select_one('a')
                if not link_tag:
                    continue
                
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.boannews.com' + link
                
                # 제목 추출
                news_txt = item.select_one('.news_txt')
                if not news_txt:
                    continue
                
                title = news_txt.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                # 중복 체크
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue
                
                news = News(
                    title=title,
                    source="보안뉴스",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    summary="",
                    category="trend",
                    url=link
                )
                db.add(news)
                count += 1
                print(f"추가: {title[:50]}...")
                
            except Exception as e:
                print(f"항목 파싱 오류: {e}")
                continue
        
        db.commit()
        return count
        
    except Exception as e:
        print(f"보안뉴스 크롤링 오류: {e}")
        return 0

def crawl_kisa(db: Session):
    """KISA 보안공지"""
    url = "https://www.boho.or.kr/kr/bbs/list.do?bbsId=B0000133"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        count = 0
        
        # 간단한 RSS 피드 사용
        rss_url = "https://www.boannews.com/media/news_rss.xml"
        response = requests.get(rss_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')[:10]
            
            for item in items:
                try:
                    title = item.find('title').text if item.find('title') else ''
                    link = item.find('link').text if item.find('link') else ''
                    
                    if not title or not link:
                        continue
                    
                    existing = db.query(News).filter(News.url == link).first()
                    if existing:
                        continue
                    
                    news = News(
                        title=title,
                        source="보안뉴스 RSS",
                        date=datetime.now().strftime("%Y-%m-%d"),
                        summary="",
                        category="trend",
                        url=link
                    )
                    db.add(news)
                    count += 1
                    print(f"RSS 추가: {title[:50]}...")
                    
                except Exception as e:
                    print(f"RSS 항목 오류: {e}")
                    continue
            
            db.commit()
        
        return count
        
    except Exception as e:
        print(f"RSS 크롤링 오류: {e}")
        return 0

def crawl_all(db: Session):
    """모든 소스 크롤링"""
    print("=== 크롤링 시작 ===")
    total = 0
    
    print("\n[1/2] 보안뉴스 크롤링...")
    total += crawl_boannews(db)
    time.sleep(2)
    
    print("\n[2/2] 보안뉴스 RSS...")
    total += crawl_kisa(db)
    
    print(f"\n=== 크롤링 완료: 총 {total}개 추가 ===")
    return total

if __name__ == "__main__":
    from database import SessionLocal
    db = SessionLocal()
    crawl_all(db)
    db.close()
