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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        news_list = soup.select('div.news_list')
        
        for item in news_list[:15]:
            try:
                title_tag = item.select_one('a.news_title')
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                link = title_tag.get('href', '')
                
                if not link.startswith('http'):
                    link = 'https://www.boannews.com' + link
                
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
                print(f"추가: {title}")
                
            except Exception as e:
                print(f"항목 파싱 오류: {e}")
                continue
        
        db.commit()
        return count
        
    except Exception as e:
        print(f"크롤링 오류: {e}")
        return 0

def crawl_krcert(db: Session):
    """한국인터넷진흥원 보안공지"""
    url = "https://www.krcert.or.kr/data/secNoticeList.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        count = 0
        
        rows = soup.select('table tbody tr')[:10]
        
        for row in rows:
            try:
                title_tag = row.select_one('td.title a')
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                link = 'https://www.krcert.or.kr' + title_tag.get('href', '')
                
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue
                
                news = News(
                    title=title,
                    source="KrCERT",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    summary="",
                    category="trend",
                    url=link
                )
                db.add(news)
                count += 1
                print(f"추가: {title}")
                
            except Exception as e:
                print(f"항목 파싱 오류: {e}")
                continue
        
        db.commit()
        return count
        
    except Exception as e:
        print(f"KrCERT 크롤링 오류: {e}")
        return 0

def crawl_all(db: Session):
    """모든 소스 크롤링"""
    print("=== 크롤링 시작 ===")
    total = 0
    
    print("\n[1/2] 보안뉴스 크롤링...")
    total += crawl_boannews(db)
    time.sleep(2)
    
    print("\n[2/2] KrCERT 크롤링...")
    total += crawl_krcert(db)
    
    print(f"\n=== 크롤링 완료: 총 {total}개 추가 ===")
    return total

if __name__ == "__main__":
    from database import SessionLocal
    db = SessionLocal()
    crawl_all(db)
    db.close()
