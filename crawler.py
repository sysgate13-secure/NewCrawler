import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from models import News, Wiki
import time
import re

# 보안 키워드 데이터베이스
SECURITY_KEYWORDS = {
    '악성코드': ['악성', '멀웨어', 'malware', '랜섬', 'ransomware', '바이러스', 'virus', 'trojan', '트로이목마', '웜', 'worm', '피싱', 'phishing', '스피어', 'spear', '해커', 'hacker', '해킹', 'hacking'],
    '취약점': ['취약', 'cve', '취약점', '취약성', 'vulnerability', '제로데이', 'zero-day', 'exploit', '익스플로잇', '보안패치', '패치', 'patch', '버그', 'bug'],
    '암호화': ['암호', 'crypto', '암호학', '암호화', 'encryption', 'rsa', 'aes', 'sha', '키노출', '해시', 'hash', '인증서', 'certificate'],
    '네트워크': ['네트워크', 'network', '방화벽', 'firewall', 'ddos', '디도스', 'botnet', '봇넷', '스캔', 'scan', '포트', 'port', '패킷', 'packet'],
    '웹보안': ['웹', 'web', 'xss', 'sql', 'sqlinjection', 'csrf', 'injection', '인젝션', '파일업로드', '경로탐색', '쿠키', 'cookie', '세션', 'session'],
    '정보보호': ['정보보호', 'security', '보안', '정보유출', '데이터유출', 'leak', 'breach', '노출', 'exposure', '침해', '침입', 'intrusion', '방어', '대응'],
}

# 간단 키워드 추출기 (보안 키워드만 필터링)
def extract_keywords(text, top_n=5):
    if not text:
        return []
    t = text.lower()
    # 보안 키워드 추출
    found_keywords = []
    for category, keywords_list in SECURITY_KEYWORDS.items():
        for kw in keywords_list:
            if kw in t:
                found_keywords.append(kw)
    
    # 중복 제거 및 빈도 계산
    freq = {}
    for kw in found_keywords:
        freq[kw] = freq.get(kw, 0) + 1
    
    # 상위 top_n 선택
    if freq:
        items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in items[:top_n]]
    return []


# 텍스트 요약 함수 (3-5줄로 자동 요약)
def summarize_text(text, target_length=100):
    """
    텍스트를 3-5줄로 요약합니다.
    """
    if not text or len(text) < 50:
        return text
    
    # 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 문장이 3-5개면 그대로 반환
    if 3 <= len(sentences) <= 5:
        return ' '.join(sentences)
    
    # 문장이 너무 많으면 처음 4-5개 문장으로 자르기
    if len(sentences) > 5:
        # 문장의 길이를 고려해서 3-5개 선택
        total_length = 0
        selected = []
        for sent in sentences:
            if total_length + len(sent) > target_length and len(selected) >= 3:
                break
            selected.append(sent)
            total_length += len(sent)
        return ' '.join(selected) if selected else ' '.join(sentences[:5])
    
    # 문장이 1-2개면 그대로 반환
    return ' '.join(sentences)


# 카테고리 키워드 매핑 (우선순위 순서대로 체크)
CATEGORY_KEYWORDS = [
    # 취약점 관련 키워드는 높은 우선순위로 검사
    ('vulnerability', ['취약', 'cve', '취약점', '취약성', '제로데이', 'zero-day', 'exploit', '익스플로잇', '보안패치', '패치']),
    # 랜섬/악성코드/피싱 등 위협(TTP) 관련
    ('malware', ['악성', '멀웨어', 'malware', '랜섬', 'ransom', 'ransomware', '바이러스', 'trojan', '악성코드', '피싱', 'phishing', '스피어피싱', '해킹', 'hacking']),
    # 네트워크/인프라
    ('network', ['네트워크', '방화벽', '라우터', '스위치', '패킷', 'tcp', 'udp', 'dDoS', '디도스', '디도스공격', '네트워크장애']),
    # 웹 관련 취약점/공격
    ('web', ['웹', '사이트', 'xss', 'sql', 'csrf', 'injection', 'sql-injection', 'cross-site', '파일업로드', '경로탐색', 'directory traversal']),
    # 암호/암호화 관련
    ('crypto', ['암호', 'crypto', 'crypt', '암호학', '암호화', 'rsa', 'aes', 'sha', '키노출', '키 탈취']),
    # 데이터 유출/정보노출은 trend/incident로 처리될 수 있음 — 우선 'trend'로 분류
    ('trend', ['유출', '데이터유출', '정보유출', 'leak', 'exposure', 'breach']),
]

# 카테고리 라벨
CATEGORY_LABELS = {
    'malware': '악성코드',
    'vulnerability': '취약점',
    'network': '네트워크',
    'web': '웹 보안',
    'crypto': '암호학',
    'trend': '기타'
}


def determine_category(text: str) -> str:
    if not text:
        return 'trend'
    t = text.lower()
    for cat, keys in CATEGORY_KEYWORDS:
        for k in keys:
            if k in t:
                return cat
    return 'trend'

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

                # 상세 페이지에서 요약(summary) 추출 시도
                summary = ""
                try:
                    article_resp = requests.get(link, headers=headers, timeout=10)
                    article_resp.encoding = 'euc-kr'
                    article_soup = BeautifulSoup(article_resp.text, 'html.parser')

                    # 시도 순서: og:description, meta description, 주요 본문의 첫 문단
                    meta_og = article_soup.find('meta', property='og:description')
                    if meta_og and meta_og.get('content'):
                        summary = meta_og.get('content').strip()
                    else:
                        meta_desc = article_soup.find('meta', attrs={'name': 'description'})
                        if meta_desc and meta_desc.get('content'):
                            summary = meta_desc.get('content').strip()
                        else:
                            # 여러 가능한 본문 선택자 시도
                            possible_selectors = [
                                'div.view_txt', 'div#view_txt', 'div.article', 'div#article',
                                'div.article_view', 'div.news_view', 'div.content', 'article',
                                '.article_con', '.view_content', '.article-body'
                            ]
                            for sel in possible_selectors:
                                node = article_soup.select_one(sel)
                                if node:
                                    # 문단들을 합쳐서 요약 생성
                                    p = node.find('p')
                                    if p and p.get_text(strip=True):
                                        summary = p.get_text(strip=True)
                                        break
                            # 마지막 대안: 첫 번째 <p> 태그
                            if not summary:
                                p_first = article_soup.find('p')
                                if p_first and p_first.get_text(strip=True):
                                    summary = p_first.get_text(strip=True)
                except Exception as e:
                    print(f"요약 추출 오류({title[:30]}...): {e}")
                    summary = ""

                # 추출한 요약을 3-5줄로 자동 요약
                if summary and len(summary) > 50:
                    summary = summarize_text(summary)

                # 중복 체크
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue
                
                # 카테고리 분류: 중앙 정의된 규칙 사용
                category = determine_category(title + ' ' + (summary or ''))

                news = News(
                    title=title,
                    source="보안뉴스",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    summary=summary or "",
                    category=category,
                    url=link
                )
                db.add(news)
                db.commit()
                
                # Wiki 테이블에 자동 추가 (제목 기준 중복 방지)
                # 위키는 뉴스와 동일한 콘텐츠가 되지 않도록 템플릿화하여 생성
                # 카테고리 라벨은 전역 매핑 사용

                wiki_existing = db.query(Wiki).filter(Wiki.title == title).first()
                if not wiki_existing:
                    wiki_preview = (summary[:200] + '...') if summary and len(summary) > 200 else (summary or '')
                    wiki_content = f"출처: 보안뉴스\n원문: {link}\n\n요약:\n{(summary or '요약이 없습니다.')}\n\n설명: 이 항목은 자동으로 생성된 위키입니다. 필요하면 편집해 주세요."
                    wiki = Wiki(
                        title=title,
                        category=CATEGORY_LABELS.get(category, category or '보안뉴스'),
                        preview=wiki_preview,
                        content=wiki_content,
                        type="auto"
                    )
                    db.add(wiki)
                    db.commit()
                
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
    """KISA RSS 크롤링"""
    url = "https://www.boho.or.kr/kr/bbs/list.do?bbsId=B0000133"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        rss_url = "https://www.boannews.com/media/news_rss.xml"
        response = requests.get(rss_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')[:10]
            count = 0
            
            for item in items:
                try:
                    title = item.find('title').text if item.find('title') else ''
                    link = item.find('link').text if item.find('link') else ''
                    
                    if not title or not link:
                        continue
                    
                    existing = db.query(News).filter(News.url == link).first()
                    if existing:
                        continue
                    
                    # RSS는 summary가 없으므로 제목 기반으로 분류
                    category = determine_category(title)

                    wiki_existing = db.query(Wiki).filter(Wiki.title == title).first()
                    if not wiki_existing:
                        # 키워드 추출로 태그 생성
                        tags = extract_keywords(title + ' ' + (summary or ''), top_n=6)
                        wiki_preview = (summary[:200] + '...') if summary and len(summary) > 200 else (summary or '')
                        wiki_content = f"출처: 보안뉴스\n원문: {link}\n\n요약:\n{(summary or '요약이 없습니다.')}\n\n설명: 이 항목은 자동으로 생성된 위키입니다. 필요하면 편집해 주세요."
                        wiki = Wiki(
                            title=title,
                            category=CATEGORY_LABELS.get(category, category or "보안뉴스"),
                            tags=','.join(tags),
                            preview=wiki_preview,
                            content=wiki_content,
                            type="auto"
                        )
                        db.add(wiki)
                        db.commit()
                    # RSS 항목으로 생성되는 위키도 템플릿화
                    if not wiki_existing:
                        tags = extract_keywords(title, top_n=5)
                        wiki_preview = ''
                        wiki_content = f"출처: 보안뉴스 RSS\n원문: {link}\n\n요약: (자동 생성된 항목)\n\n설명: 이 항목은 RSS에서 자동 생성되었습니다. 필요하면 편집해 주세요."
                        wiki = Wiki(
                            title=title,
                            category=category_labels.get(category, category or "보안뉴스 RSS"),
                            tags=','.join(tags),
                            preview=wiki_preview,
                            content=wiki_content,
                            type="auto"
                        )
                        db.add(wiki)
                        db.commit()
                    
                    count += 1
                    print(f"RSS 추가: {title[:50]}...")
                    
                except Exception as e:
                    print(f"RSS 항목 오류: {e}")
                    continue
            
            return count
        
        return 0
        
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
