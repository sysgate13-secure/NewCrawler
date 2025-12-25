# 🔒 보안 뉴스 크롤링 & 지식 공유 플랫폼

매일 자동으로 보안 뉴스를 수집하고, AI로 요약하며, 학습한 보안 지식을 체계적으로 정리하는 **포트폴리오용** 플랫폼

## ✨ 주요 기능

### 🤖 자동화
- **자동 크롤링**: 매일 오전 8시 GitHub Actions로 자동 실행
- **AI 요약**: OpenAI API로 뉴스 자동 요약 생성

### 🔍 검색
- **Elasticsearch**: 한글 형태소 분석 (Nori) 기반 전문 검색
- **통합 검색**: 뉴스와 지식 사전 동시 검색

### 📚 지식 관리
- **실제 보안 지식**: SQL Injection, XSS, CSRF, Zero Trust 등
- **Markdown 지원**: 코드 블록, 표, 리스트 등
- **웹 편집**: 브라우저에서 직접 작성

### 📊 데이터 수집
- 보안뉴스 (boannews.com)
- KrCERT 보안공지
- RSS 피드

## 🏗️ 기술 스택

| 분야 | 기술 |
|------|------|
| **Backend** | FastAPI, Python 3.11 |
| **Database** | SQLite, SQLAlchemy |
| **Search** | Elasticsearch 8.11 + Nori |
| **AI** | OpenAI GPT-3.5 Turbo |
| **Crawler** | BeautifulSoup4, Requests |
| **Deploy** | Docker Compose |
| **CI/CD** | GitHub Actions |

## 🚀 빠른 시작

### 방법 1: Docker Compose (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/sysgate13-secure/NewCrawler.git
cd NewCrawler

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집: OPENAI_API_KEY 입력

# 3. Docker Compose 실행
docker-compose up -d

# 4. 보안 지식 추가
docker-compose exec app python add_security_knowledge.py

# 5. 접속
http://localhost:8000
```

### 방법 2: 로컬 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. Elasticsearch 실행 (별도)
docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.11.0

# 3. 환경 변수 설정
cp .env.example .env
# OPENAI_API_KEY 입력

# 4. DB 초기화 및 지식 추가
python init_db.py
python add_security_knowledge.py

# 5. 서버 실행
uvicorn main:app --reload

# 6. 접속
http://localhost:8000
```

## 📁 프로젝트 구조

```
security-news-platform/
├── main.py                      # FastAPI 서버
├── crawler.py                   # 크롤러 (보안뉴스, RSS)
├── models.py                    # DB 모델
├── database.py                  # DB 연결
├── elasticsearch_client.py      # ES 클라이언트
├── ai_summarizer.py             # AI 요약
├── add_security_knowledge.py    # 보안 지식 추가
├── docker-compose.yml           # Docker 설정
├── Dockerfile
├── requirements.txt
├── .github/workflows/
│   └── crawler.yml              # 자동 크롤링
└── templates/
    ├── index.html               # 메인
    ├── wiki_manage.html         # 위키 관리
    └── wiki_detail.html         # 위키 상세

```

## 🎯 주요 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/` | 메인 페이지 |
| GET | `/api/news` | 뉴스 목록 |
| GET | `/api/wiki` | 위키 목록 |
| GET | `/api/search?q=검색어` | 통합 검색 (ES) |
| POST | `/api/crawl` | 크롤링 즉시 실행 |
| POST | `/api/news/{id}/summarize` | AI 요약 생성 |
| POST | `/api/wiki/add` | 위키 추가 |
| GET | `/wiki/{id}` | 위키 상세 |
| GET | `/wiki/manage` | 위키 관리 페이지 |
| GET | `/health` | 헬스 체크 |

## 🔄 GitHub Actions 자동화

매일 한국시간 오전 8시(UTC 23시)에 자동으로 크롤링 실행

- **스케줄**: `0 23 * * *`
- **수동 실행**: Actions 탭에서 'Run workflow'
- **자동 커밋**: 새 뉴스 수집 시 자동 push

## 📝 위키 작성 가이드

1. `http://localhost:8000/wiki/manage` 접속
2. 제목, 카테고리, 타입 선택
3. Markdown 형식으로 작성
4. 저장 시 자동으로 Elasticsearch 인덱싱

### 지원 Markdown
- 제목: `##`, `###`
- 코드 블록: ` ```python ... ``` `
- 인라인 코드: `` `code` ``
- 리스트: `- item` 또는 `1. item`
- 표: 일반 Markdown 테이블

## 🔍 Elasticsearch 검색

### 한글 형태소 분석 (Nori)
- "랜섬웨어 공격" → "랜섬", "웨어", "공격" 분리
- 띄어쓰기 오류 허용
- 관련도 점수 기반 정렬

### 검색 필드 가중치
- 제목: 3배 가중치
- 요약/내용: 1배

## 🤖 AI 요약 기능

OpenAI GPT-3.5 Turbo 사용
- 뉴스 제목 → 50자 이내 한 줄 요약
- 자동 카테고리 분류 (예정)
- 키워드 추출 (예정)

## 🗄️ 데이터베이스 스키마

### News
```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    date TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    url TEXT UNIQUE,
    created_at DATETIME
);
```

### Wiki
```sql
CREATE TABLE wiki (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    preview TEXT,
    content TEXT,
    type TEXT,
    created_at DATETIME
);
```

## 📊 포트폴리오 강점

### 1. 최신 기술 스택
- Elasticsearch (전문 검색)
- OpenAI API (AI 통합)
- Docker (컨테이너화)
- GitHub Actions (CI/CD)

### 2. 실무 시나리오
- 자동 크롤링 → 데이터 수집
- AI 요약 → 자동화
- 검색 최적화 → 사용자 경험

### 3. 보안 도메인 지식
- SQL Injection, XSS, CSRF
- Zero Trust, DDoS
- Ransomware, OWASP Top 10

## 🐛 트러블슈팅

### Elasticsearch 연결 실패
```bash
# ES 상태 확인
curl http://localhost:9200

# 컨테이너 재시작
docker-compose restart elasticsearch
```

### OpenAI API 오류
- `.env` 파일에 올바른 API 키 입력
- API 사용량 확인

### 크롤링 실패
- 인터넷 연결 확인
- 대상 사이트 구조 변경 가능성

## 📈 향후 개선 계획

- [ ] 뉴스 자동 분류 (ML)
- [ ] 대시보드 고도화 (차트)
- [ ] 사용자 인증 시스템
- [ ] 댓글/토론 기능
- [ ] 북마크/즐겨찾기
- [ ] RSS 구독 기능
- [ ] Webhook 알림

## 📄 라이선스

MIT License

## 👨‍💻 개발자

- GitHub: [@sysgate13-secure](https://github.com/sysgate13-secure)
- Email: 250818752+sysgate13-secure@users.noreply.github.com
