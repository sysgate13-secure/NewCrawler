"""
데이터 정제 유틸리티
위키 콘텐츠에서 핵심 정보만 추출
"""
import re

def clean_markdown(text):
    """마크다운 문법 제거"""
    if not text:
        return ""
    
    # 코드 블록 제거
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # 인라인 코드 제거
    text = re.sub(r'`[^`]+`', '', text)
    
    # 헤더 마크 제거 (##, ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 리스트 마크 제거 (-, *, 1.)
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # 볼드/이탤릭 제거
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # 링크 제거 [텍스트](url) -> 텍스트
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 여러 줄바꿈을 하나로
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def extract_summary(content, max_sentences=3):
    """첫 N개 문장만 추출"""
    if not content:
        return ""
    
    # 마크다운 정제
    clean_text = clean_markdown(content)
    
    # 문장 단위로 분리 (., !, ? 기준)
    sentences = re.split(r'[.!?]\s+', clean_text)
    
    # 빈 문장 제거
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # 첫 N개 문장만
    summary_sentences = sentences[:max_sentences]
    
    return '. '.join(summary_sentences) + '.'

def extract_key_points(content, max_points=5):
    """리스트 항목에서 핵심 포인트만 추출"""
    if not content:
        return []
    
    # 리스트 항목 찾기
    list_items = re.findall(r'^[\-\*]\s+(.+)$', content, flags=re.MULTILINE)
    list_items += re.findall(r'^\d+\.\s+(.+)$', content, flags=re.MULTILINE)
    
    # 마크다운 정제
    clean_items = [clean_markdown(item) for item in list_items]
    
    # 빈 항목 제거
    clean_items = [item for item in clean_items if item and len(item) > 5]
    
    # 최대 N개만
    return clean_items[:max_points]

def truncate_text(text, max_length=200):
    """텍스트 길이 제한"""
    if not text:
        return ""
    
    text = text.strip()
    if len(text) <= max_length:
        return text
    
    # 마지막 공백 기준으로 자르기
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + '...'

def extract_concept(content):
    """개념 설명 부분만 추출 (첫 번째 섹션)"""
    if not content:
        return ""
    
    # 첫 번째 ## 헤더까지만
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
    
    if len(sections) > 1:
        first_section = sections[1].split('\n\n')[0]  # 첫 문단만
        return clean_markdown(first_section)
    
    
    return extract_summary(content, max_sentences=2)

def get_wiki_preview(wiki, mode='short'):
    """
    위키 객체에서 표시용 미리보기 생성
    
    mode:
        - 'short': 50자 이내 짧은 요약
        - 'medium': 150자 이내 중간 요약
        - 'long': 300자 이내 긴 요약
    """
    content = wiki.content or wiki.preview or ""
    
    if mode == 'short':
        # 핵심 개념만
        concept = extract_concept(content)
        return truncate_text(concept, max_length=80)
    
    elif mode == 'medium':
        # 2-3문장
        summary = extract_summary(content, max_sentences=2)
        return truncate_text(summary, max_length=150)
    
    elif mode == 'long':
        # 전체 요약
        summary = extract_summary(content, max_sentences=4)
        return truncate_text(summary, max_length=300)
    
    return wiki.preview or ""

def get_wiki_highlights(wiki):
    """위키에서 하이라이트 포인트 추출"""
    content = wiki.content or ""
    
    highlights = {
        'concept': extract_concept(content),
        'key_points': extract_key_points(content, max_points=3),
        'summary': extract_summary(content, max_sentences=2)
    }
    
    return highlights

def format_for_display(text, remove_technical=False):
    """화면 표시용 텍스트 포맷팅"""
    if not text:
        return ""
    
    text = clean_markdown(text)
    
    if remove_technical:
        # 기술적 용어 간소화 (선택적)
        text = re.sub(r'\([^)]*bit\)', '', text)  # (2048bit) 같은 표현 제거
        text = re.sub(r'v?\d+\.\d+\.\d+', '', text)  # 버전 번호 제거
    
    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_attack_method(content):
    """공격 방법 섹션만 추출"""
    if not content:
        return ""
    
    # "공격 예시", "공격 시나리오" 등의 섹션 찾기
    attack_section = re.search(r'### 공격.*?\n([\s\S]*?)(?=###|\n\n##|$)', content)
    if attack_section:
        return clean_markdown(attack_section.group(1))
    
    return ""

def extract_defense_method(content):
    """방어 방법 섹션만 추출"""
    if not content:
        return ""
    
    # "방어 방법", "대응 방법" 등의 섹션 찾기
    defense_section = re.search(r'### 방어.*?\n([\s\S]*?)(?=###|\n\n##|$)', content)
    if defense_section:
        points = extract_key_points(defense_section.group(1))
        return points
    
    return []

# 뉴스 요약용 함수
def clean_news_summary(summary):
    """뉴스 요약 정제"""
    if not summary:
        return ""
    
    # 불필요한 접두사 제거
    summary = re.sub(r'^(요약:|Summary:)\s*', '', summary)
    
    # 따옴표 제거
    summary = summary.strip('"\'')
    
    return summary.strip()


if __name__ == "__main__":
    # 테스트
    test_content = """## SQL Injection이란?

SQL 인젝션은 웹 애플리케이션의 입력값 검증이 부족할 때 발생하는 공격입니다. 공격자가 SQL 쿼리의 일부로 악의적인 코드를 삽입하여 데이터베이스를 조작합니다.

### 공격 예시
```python
query = f"SELECT * FROM users WHERE id = '{user_id}'"
```

### 방어 방법
1. **Prepared Statement 사용**
2. **입력값 검증**
3. **WAF 사용**
"""

    print("=== 테스트 ===\n")
    
    print("1. 마크다운 정제:")
    print(clean_markdown(test_content))
    print("\n" + "="*50 + "\n")
    
    print("2. 요약 추출 (2문장):")
    print(extract_summary(test_content, max_sentences=2))
    print("\n" + "="*50 + "\n")
    
    print("3. 핵심 포인트:")
    points = extract_key_points(test_content)
    for i, point in enumerate(points, 1):
        print(f"  {i}. {point}")
    print("\n" + "="*50 + "\n")
    
    print("4. 개념 추출:")
    print(extract_concept(test_content))
