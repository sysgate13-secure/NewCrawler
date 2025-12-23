# 보안 뉴스 크롤링 & 지식 공유 플랫폼

매일 자동으로 보안 뉴스를 수집하고 학습한 보안 지식을 체계적으로 정리하는 플랫폼

## ✨ 주요 기능

- 🤖 **자동 크롤링**: 매일 오전 8시 자동으로 보안 뉴스 수집
- 📰 **뉴스 수집**: 보안뉴스, KrCERT 보안공지 크롤링
- 📚 **지식 사전**: 보안 개념 정리 및 저장
- 📊 **대시보드**: 통계 및 현황 한눈에 확인
- 🔍 **검색**: 뉴스와 지식 문서 통합 검색

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/sysgate13-secure/NewCrawler.git
cd NewCrawler
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. DB 초기화
```bash
python init_db.py
```

### 4. 서버 실행
```bash
uvicorn main:app --reload
```

### 5. 브라우저 접속
```
http://localhost:8000
```

## 📁 프로젝트 구조

```
security-news-platform/
├── main.py              # FastAPI 서버
├── crawler.py           # 크롤러 (보안뉴스, KrCERT)
├── models.py            # DB 모델
├── database.py          # DB 연결
├── init_db.py           # 초기 데이터 설정
├── requirements.txt
├── .github/
│   └── workflows/
│       └── crawler.yml  # GitHub Actions
└── templates/
    ├── index.html       # 메인 페이지
    └── wiki_manage.html # 위키 관리 페이지
```

## 🔄 GitHub Actions 자동 크롤링

매일 한국시간 오전 8시(UTC 23시)에 자동으로 크롤링이 실행됩니다.

- **스케줄**: `0 23 * * *` (매일 UTC 23시)
- **수동 실행**: Actions 탭에서 'Run workflow' 버튼으로 즉시 실행 가능

## 📝 위키 관리

`http://localhost:8000/wiki/manage` 에서 새로운 보안 지식 문서를 추가할 수 있습니다.

### 카테고리
- 웹 보안
- 네트워크 보안
- 암호학
- 악성코드
- 최신 트렌드

## 🛠 기술 스택

- **언어**: Python 3.11
- **프레임워크**: FastAPI
- **크롤링**: BeautifulSoup4, Requests
- **데이터베이스**: SQLite
- **템플릿**: Jinja2
- **자동화**: GitHub Actions

## 📊 API 엔드포인트

- `GET /`: 메인 페이지
- `GET /api/news`: 뉴스 목록 조회
- `GET /api/wiki`: 위키 목록 조회
- `POST /api/crawl`: 크롤링 즉시 실행
- `GET /wiki/manage`: 위키 관리 페이지
- `POST /api/wiki/add`: 위키 추가

## 📄 라이선스

MIT License
