# 🚀 빠른 시작 가이드

## Elasticsearch 없이 테스트 (빠른 시작)

```bash
# 1. 패키지 설치
pip install fastapi uvicorn beautifulsoup4 requests sqlalchemy jinja2 python-multipart lxml python-dotenv

# 2. DB 초기화
python init_db.py

# 3. 보안 지식 추가
python add_security_knowledge.py

# 4. 크롤링 테스트
python crawler.py

# 5. 서버 실행
uvicorn main:app --reload

# 6. 브라우저
http://localhost:8000
```

Elasticsearch와 AI 요약 없이도 **기본 기능은 모두 작동**합니다!

## Elasticsearch + AI 풀 기능

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 입력

# 2. Docker Compose로 실행
docker-compose up -d

# 3. 보안 지식 추가 (컨테이너 내부)
docker-compose exec app python add_security_knowledge.py

# 4. 접속
http://localhost:8000
```

## 주요 페이지

- 메인: http://localhost:8000
- 위키 관리: http://localhost:8000/wiki/manage
- 헬스 체크: http://localhost:8000/health
- API 문서: http://localhost:8000/docs

## 테스트 순서

1. ✅ 메인 페이지 → 샘플 뉴스 확인
2. ✅ 위키 → 8개 보안 지식 문서 확인
3. ✅ 크롤링 실행 → 실제 뉴스 수집
4. ✅ 검색 → 키워드 검색 테스트
5. ✅ 위키 관리 → 새 문서 작성

## Git 푸시

```bash
git push -u origin main
```
