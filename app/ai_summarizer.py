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
1. 반드시 한국어로 작성할 것. (한자 실수를 방지하기 위해 '勒'과 같은 한자 대신 '랜섬웨어'라고 작성)
2. '누가, 어떤 취약점으로, 어떤 피해를 입었는지'를 포함할 것.
3. 전문 용어는 가급적 유지하되 문장은 매끄럽게 '~함', '~임' 체로 끝낼 것.
4. **절대 한자(Chinese characters)를 사용하지 말 것.** (예: '勒'(랜섬), '蜘蛛'(크롤러/스파이더), '歌曲'(음악/곡) 등 금지)
5. 최대 2문장으로 압축할 것."""

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
    """LM Studio를 사용하여 지식 사전(Wiki) 상세 내용 생성"""
    try:
        prompt = f"""보안 주제 '{title}'에 대해 지식 사전용 콘텐츠를 전문적이고 상세하게 작성해줘.
카테고리: {category}

다음 세 가지 섹션을 반드시 포함하여 작성할 것:
1. 기술 설명 (Short Explanation): 이 기술이나 개념의 핵심 정의와 배경을 2-3문장으로 설명.
2. 공격 방식 (Attack Methods): 이와 관련된 공격 방식, 취약점 활용 시나리오 또는 위협 요소를 상세히 설명.
3. 방어 및 보안 (Defense & Security): 실무자가 적용해야 할 구체적인 방어 조치, 보안 설정 또는 대응 전략.

작성 규칙:
- 반드시 한국어로만 작성할 것.
- '勒'(랜섬), '索'(소)와 같은 한자를 절대 포함하지 말고 '랜섬웨어' 또는 '한국어 보안 용어'를 사용할 것.

각 섹션은 명확한 제목과 함께 매끄러운 한국어 문장으로 작성할 것."""

        payload = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "당신은 보안 지식 사전을 집필하는 시니어 보안 아키텍트입니다. 모든 답변은 한자(Chinese characters) 없이 순수 한국어로만 작성해야 합니다. 한자어는 한자를 쓰지 말고 한글로만 표기하십시오."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
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