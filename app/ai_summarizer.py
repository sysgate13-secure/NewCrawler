import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# LM Studio 로컬 서버 설정
LM_STUDIO_URL = "http://localhost:12345/v1/chat/completions"

def summarize_news(title, content=None):
    """LM Studio를 사용하여 뉴스 제목과 본문을 기반으로 핵심 요약 생성"""
    try:
        source_text = content if content else title
        
        prompt = f"""아래의 보안 뉴스 내용을 지식 사전에 등록할 수 있도록 핵심만 요약해줘.
        
내용: {source_text[:1500]}

작성 규칙:
1. 반드시 한국어로 작성할 것.
2. '누가, 어떤 취약점으로, 어떤 피해를 입었는지'를 포함할 것.
3. 전문 용어는 가급적 유지하되 문장은 매끄럽게 '~함', '~임' 체로 끝낼 것.
4. 최대 2문장으로 압축할 것."""

        payload = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "당신은 보안 뉴스를 분석하고 핵심을 요약하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(LM_STUDIO_URL, data=json.dumps(payload), headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        summary = result['choices'][0]['message']['content'].strip()
        return summary
        
    except Exception as e:
        print(f"로컬 AI 요약 생성 오류: {e}")
        return ""

def generate_wiki_content(title, category):
    """LM Studio를 사용하여 위키 상세 내용 생성"""
    try:
        prompt = f"""보안 주제 '{title}'에 대해 지식 사전용 콘텐츠를 작성해줘.
카테고리: {category}

다음 형식에 맞춰 전문적으로 작성해줘:
1. 개념 설명: 이 기술이나 위협의 핵심 정의
2. 위험성: 보안 측면에서 발생하는 주요 문제점
3. 대응 방법: 실무자가 적용할 수 있는 방어 대책

각 섹션은 2문장 내외로 명확하게 작성할 것."""

        payload = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "당신은 보안 지식 사전을 집필하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.5
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(LM_STUDIO_URL, data=json.dumps(payload), headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        return content
        
    except Exception as e:
        print(f"로컬 AI 위키 생성 오류: {e}")
        return None