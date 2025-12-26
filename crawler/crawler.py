import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import News, Wiki
from app.ai_summarizer import summarize_news, generate_wiki_content
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

                # 카테고리 분류: 중앙 정의된 규칙 사용
                category = determine_category(title + ' ' + (summary or ''))

                # 중복 체크
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue

                # AI 요약 시도
                ai_summary = summarize_news(title, summary)
                if ai_summary:
                    processed_summary = ai_summary
                elif summary and len(summary) > 50:
                    # AI 실패 시 기존 텍스트 기반 요약
                    processed_summary = summarize_text(summary)
                else:
                    processed_summary = summary or ""

                news = News(
                    title=title,
                    source="보안뉴스",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    summary=processed_summary,
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
                    # AI 위키 콘텐츠 생성
                    wiki_cat = CATEGORY_LABELS.get(category, category or '기타')
                    wiki_content = generate_wiki_content(title, wiki_cat)
                    
                    if not wiki_content:
                        # AI 실패 시 폴백
                        wiki_content = f"출처: 보안뉴스\n원문: {link}\n\n요약:\n{(processed_summary or '요약 없음')}"
                    
                    wiki = Wiki(
                        title=title,
                        category=wiki_cat,
                        preview=(processed_summary[:200] + '...') if processed_summary and len(processed_summary) > 200 else (processed_summary or ''),
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

def crawl_krcert(db: Session):
    """KrCERT 보안공지 크롤링"""
    url = "https://www.krcert.or.kr/data/secNoticeList.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # KrCERT 테이블에서 뉴스 추출
        table = soup.find('table', class_='artclTable')
        if table:
            rows = table.find_all('tr')[1:11]  # 상위 10개
            count = 0
            
            for row in rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 2:
                        continue
                    
                    title_elem = cols[0].find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    if not link.startswith('http'):
                        link = 'https://www.krcert.or.kr' + link
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # 중복 체크
                    existing = db.query(News).filter(News.url == link).first()
                    if existing:
                        continue
                    
                    # 상세 페이지에서 요약 추출
                    summary = ""
                    try:
                        article_resp = requests.get(link, headers=headers, timeout=10)
                        article_resp.encoding = 'utf-8'
                        article_soup = BeautifulSoup(article_resp.text, 'html.parser')
                        
                        content_div = article_soup.find('div', class_='cont')
                        if content_div:
                            p = content_div.find('p')
                            if p:
                                summary = p.get_text(strip=True)[:300]
                    except:
                        pass
                    
                    category = determine_category(title + ' ' + (summary or ''))
                    
                    news = News(
                        title=title,
                        url=link,
                        source="KrCERT",
                        summary=summary or "",
                        category=category
                    )
                    db.add(news)
                    db.commit()
                    
                    count += 1
                    print(f"KrCERT 추가: {title[:50]}...")
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"KrCERT 항목 오류: {e}")
                    continue
            
            return count
        
        return 0
        
    except Exception as e:
        print(f"KrCERT 크롤링 오류: {e}")
        return 0

def crawl_zdnet(db: Session):
    """ZDNet 보안 뉴스 크롤링"""
    url = "https://www.zdnet.co.kr/news/security/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ZDNet 기사 찾기
        articles = soup.find_all('article', class_='card-item')[:10]
        count = 0
        
        for article in articles:
            try:
                title_elem = article.find('h2')
                link_elem = article.find('a')
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                
                if not link.startswith('http'):
                    link = 'https://www.zdnet.co.kr' + link
                
                if not title or len(title) < 5:
                    continue
                
                # 중복 체크
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue
                
                # 요약 추출
                summary_elem = article.find('p', class_='desc')
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                category = determine_category(title + ' ' + (summary or ''))
                
                news = News(
                    title=title,
                    url=link,
                    source="ZDNet",
                    summary=summary[:300] if summary else "",
                    category=category
                )
                db.add(news)
                db.commit()
                
                count += 1
                print(f"ZDNet 추가: {title[:50]}...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"ZDNet 항목 오류: {e}")
                continue
        
        return count
        
    except Exception as e:
        print(f"ZDNet 크롤링 오류: {e}")
        return 0

def crawl_cisa(db: Session):
    """CISA (미국 사이버보안청) 공지 크롤링"""
    url = "https://www.cisa.gov/news-events/alerts"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CISA 알림 찾기
        alerts = soup.find_all('div', class_='alert-item')[:10]
        count = 0
        
        for alert in alerts:
            try:
                title_elem = alert.find('h3')
                link_elem = alert.find('a')
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                
                if not link.startswith('http'):
                    link = 'https://www.cisa.gov' + link
                
                if not title or len(title) < 5:
                    continue
                
                # 중복 체크
                existing = db.query(News).filter(News.url == link).first()
                if existing:
                    continue
                
                summary_elem = alert.find('p')
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                category = determine_category(title + ' ' + (summary or ''))
                
                news = News(
                    title=title,
                    url=link,
                    source="CISA",
                    summary=summary[:300] if summary else "",
                    category=category
                )
                db.add(news)
                db.commit()
                
                count += 1
                print(f"CISA 추가: {title[:50]}...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"CISA 항목 오류: {e}")
                continue
        
        return count
        
    except Exception as e:
        print(f"CISA 크롤링 오류: {e}")
        return 0


# 범용 크롤러 헬퍼 및 해외 사이트 크롤러들
def _generic_crawl(db: Session, list_url: str, domain: str, source_label: str, 
                   title_selector: str = None, summary_selector: str = None, max_items: int = 8):
    """범용 크롤러: 리스트 페이지에서 링크 추출 후 제목/요약을 수집합니다."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(list_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        links = []
        # 셀렉터가 제공된 경우 해당 요소들에서 링크 추출
        if title_selector:
            for item in soup.select(title_selector):
                a = item if item.name == 'a' else item.find('a')
                if a and a.get('href'):
                    href = a['href']
                    if href.startswith('/'): href = requests.compat.urljoin(list_url, href)
                    if domain in href and href not in links: links.append(href)
        else:
            # 기본 링크 추출 로직
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/'): href = requests.compat.urljoin(list_url, href)
                if domain in href and href not in links: links.append(href)

        selected = []
        for l in links:
            if any(x in l for x in ['#', '/tag/', '/category/', '/comments', '/page/', '?']): continue
            if l not in selected: selected.append(l)
            if len(selected) >= max_items: break

        added = 0
        for link in selected:
            try:
                aresp = requests.get(link, headers=headers, timeout=10)
                aresp.raise_for_status()
                asoup = BeautifulSoup(aresp.text, 'html.parser')

                # 제목 추출
                title = None
                meta_og = asoup.find('meta', property='og:title')
                if meta_og: title = meta_og.get('content', '').strip()
                if not title:
                    h1 = asoup.find('h1')
                    if h1: title = h1.get_text(strip=True)
                if not title: continue

                # 요약 추출
                summary = ''
                # 1. 인자로 받은 요약 셀렉터 시도 (리스트 페이지에서 가져오는 것이 더 나을 수도 있으나 여기선 상세 페이지 기준)
                if summary_selector:
                    s_node = asoup.select_one(summary_selector)
                    if s_node: summary = s_node.get_text(strip=True)
                
                if not summary:
                    meta_desc = asoup.find('meta', attrs={'name': 'description'}) or asoup.find('meta', property='og:description')
                    if meta_desc: summary = meta_desc.get('content', '').strip()
                
                if not summary:
                    p = asoup.find('p')
                    if p: summary = p.get_text(strip=True)

                category = determine_category(title + ' ' + (summary or ''))
                existing = db.query(News).filter(News.url == link).first()
                if existing: continue

                # AI 요약 시도
                ai_summary = summarize_news(title, summary)
                if ai_summary:
                    processed_summary = ai_summary
                else:
                    processed_summary = summarize_text(summary) if summary else ""

                news = News(
                    title=title, source=source_label, date=datetime.now().strftime("%Y-%m-%d"),
                    summary=processed_summary,
                    category=category, url=link
                )
                db.add(news)
                db.commit()

                # 위키 자동 생성
                wiki_existing = db.query(Wiki).filter(Wiki.title == title).first()
                if not wiki_existing:
                    wiki_cat = CATEGORY_LABELS.get(category, '기타')
                    wiki_content = generate_wiki_content(title, wiki_cat)
                    
                    if not wiki_content:
                        wiki_content = f"출처: {source_label}\n원문: {link}\n\n요약:\n{processed_summary or '요약 없음'}"
                        
                    wiki = Wiki(
                        title=title, category=wiki_cat,
                        preview=(processed_summary[:200] + '...') if processed_summary and len(processed_summary) > 200 else (processed_summary or ''),
                        content=wiki_content,
                        type="auto"
                    )
                    db.add(wiki)
                    db.commit()

                added += 1
                print(f"{source_label} 추가: {title[:50]}...")
                time.sleep(0.5)
            except Exception as e:
                print(f"{source_label} 항목 오류: {e}")
                continue
        return added
    except Exception as e:
        print(f"{source_label} 크롤링 오류: {e}")
        return -1

def crawl_cyberscoop(db: Session):
    return _generic_crawl(db, 'https://cyberscoop.com/news/', 'cyberscoop.com', 'CyberScoop', 
                        title_selector='.post-item__title-link', summary_selector='.post-item__excerpt')

def crawl_helpnetsecurity(db: Session):
    return _generic_crawl(db, 'https://www.helpnetsecurity.com/view/news/', 'helpnetsecurity.com', 'HelpNetSecurity', 
                        title_selector='.card-title a')

def crawl_hackread(db: Session):
    return _generic_crawl(db, 'https://hackread.com/', 'hackread.com', 'HackRead', 
                        title_selector='.cs-entry__title a', summary_selector='.cs-entry__excerpt')

def crawl_infosecurity(db: Session):
    return _generic_crawl(db, 'https://www.infosecurity-magazine.com/news/', 'infosecurity-magazine.com', 'InfoSecurity', 
                        title_selector='.webpage-title a', summary_selector='.webpage-summary')

def crawl_all(db: Session):
    """모든 소스 크롤링"""
    print("=== 크롤링 시작 ===")
    total = 0

    print("\n[1] 보안뉴스 크롤링...")
    res = crawl_boannews(db)
    if res != -1: total += res
    time.sleep(1)

    # 새로운 해외 보안 뉴스 소스
    overseas = [
        (crawl_cyberscoop, 'CyberScoop'),
        (crawl_helpnetsecurity, 'HelpNetSecurity'),
        (crawl_hackread, 'HackRead'),
        (crawl_infosecurity, 'InfoSecurity Magazine'),
    ]

    idx = 2
    for func, name in overseas:
        print(f"\n[{idx}] {name} 크롤링...")
        try:
            r = func(db)
            if r != -1: total += r
            time.sleep(1)
        except Exception as e:
            print(f"{name} 오류: {e}")
        idx += 1

    print(f"\n=== 크롤링 완료: 총 {total}개 추가 ===")
    return total

if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    crawl_all(db)
    db.close()
