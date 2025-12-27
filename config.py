"""
설정 파일
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Elasticsearch 설정
ES_ENABLED = os.getenv("ES_ENABLED", "false").lower() == "true"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
