# 📊 데이터 정제 유틸리티

## 기능

위키 콘텐츠와 뉴스 요약에서 **핵심 정보만 추출**하여 표시합니다.

## 제공 함수

### 1. 마크다운 정제
```python
from data_utils import clean_markdown

# 코드 블록, 헤더, 리스트 마크 등 제거
clean_text = clean_markdown(wiki.content)
```

### 2. 요약 추출
```python
from data_utils import extract_summary

# 첫 N개 문장만 추출
summary = extract_summary(wiki.content, max_sentences=3)
```

### 3. 핵심 포인트 추출
```python
from data_utils import extract_key_points

# 리스트 항목에서 핵심만
points = extract_key_points(wiki.content, max_points=5)
```

### 4. 위키 미리보기 (자주 사용)
```python
from data_utils import get_wiki_preview

# 3가지 모드
short = get_wiki_preview(wiki, mode='short')    # 80자 이내
medium = get_wiki_preview(wiki, mode='medium')  # 150자 이내  
long = get_wiki_preview(wiki, mode='long')      # 300자 이내
```

### 5. 하이라이트 정보
```python
from data_utils import get_wiki_highlights

highlights = get_wiki_highlights(wiki)
# {
#   'concept': '핵심 개념',
#   'key_points': ['포인트1', '포인트2', ...],
#   'summary': '전체 요약'
# }
```

## 템플릿에서 사용

### Jinja2 필터로 자동 적용
```html
<!-- 짧은 미리보기 (80자) -->
<p>{{ wiki | wiki_preview('short') }}</p>

<!-- 중간 미리보기 (150자) -->
<p>{{ wiki | wiki_preview('medium') }}</p>

<!-- 뉴스 요약 정제 -->
<p>{{ news.summary | clean_summary }}</p>
```

## 적용 효과

### Before (정제 전)
```
## SQL Injection이란?

SQL 인젝션은 웹 애플리케이션의 입력값 검증이 부족할 때 발생...

### 공격 예시
```python
query = f"SELECT * FROM..."
```

### 방어 방법
1. **Prepared Statement 사용**
2. **입력값 검증**
...
```

### After (정제 후)
```
SQL 인젝션은 웹 애플리케이션의 입력값 검증이 부족할 때 
발생하는 공격입니다. 공격자가 SQL 쿼리의 일부로 악의적인 
코드를 삽입하여 데이터베이스를 조작합니다.
```

## 장점

✅ **가독성 향상**: 불필요한 코드/마크다운 제거
✅ **일관성**: 모든 위키가 동일한 형식으로 표시
✅ **성능**: 렌더링 속도 개선
✅ **UX**: 핵심 정보 빠른 파악

## 사용 예시

### 메인 페이지
- **짧은 미리보기 (80자)**: 카드 형태로 표시

### 검색 결과
- **중간 미리보기 (150자)**: 검색어 매칭 내용

### 상세 페이지  
- **전체 내용**: 마크다운 렌더링

## 커스터마이징

`data_utils.py`에서 길이 조정:
```python
def get_wiki_preview(wiki, mode='short'):
    if mode == 'short':
        return truncate_text(concept, max_length=80)  # 조정 가능
```
