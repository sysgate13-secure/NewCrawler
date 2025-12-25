import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_news(title, url=None):
    """뉴스 제목을 기반으로 AI 요약 생성"""
    if not openai.api_key:
        return "API 키가 설정되지 않았습니다."
    
    try:
        prompt = f"""다음 보안 뉴스 제목을 한 줄로 요약해주세요 (50자 이내):

제목: {title}

요약은 핵심 내용만 간단명료하게 작성해주세요."""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 보안 뉴스를 요약하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        print(f"요약 생성 오류: {e}")
        return ""

def generate_wiki_content(title, category):
    """위키 내용 자동 생성"""
    if not openai.api_key:
        return None
    
    try:
        prompt = f"""다음 보안 주제에 대해 초보자가 이해할 수 있도록 설명해주세요:

주제: {title}
카테고리: {category}

다음 형식으로 작성해주세요:
1. 개념 설명
2. 위험성
3. 실제 사례
4. 방어 방법

각 섹션은 2-3문장으로 간단히 작성해주세요."""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 보안 전문가이자 교육자입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        return content
        
    except Exception as e:
        print(f"콘텐츠 생성 오류: {e}")
        return None
