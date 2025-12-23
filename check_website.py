"""
웹사이트 HTML 구조 확인 스크립트
"""
import requests
from bs4 import BeautifulSoup

def check_boannews():
    print("=== 보안뉴스 확인 ===")
    url = "https://www.boannews.com/media/t_list.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 다양한 선택자 시도
        selectors = [
            'div.news_list',
            '.news_list',
            'div.news_line',
            '.news_line',
            'a.news_title',
            '.news_title'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"{selector}: {len(items)}개 발견")
            
            if items and len(items) > 0:
                print(f"첫 번째 항목 HTML:")
                print(str(items[0])[:200])
                print()
                
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    check_boannews()
