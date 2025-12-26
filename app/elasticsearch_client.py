from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

def get_es_client():
    """Elasticsearch 클라이언트 생성 (연결 타임아웃 설정)"""
    return Elasticsearch([ES_URL], request_timeout=5)

def create_indices():
    """인덱스 생성 (한글 형태소 분석기 nori 사용)"""
    es = get_es_client()
    
    # 뉴스 인덱스 설정
    news_index = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "nori_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "analyzer": "nori_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "source": {"type": "keyword"},
                "date": {"type": "date", "format": "yyyy-MM-dd"},
                "summary": {
                    "type": "text",
                    "analyzer": "nori_analyzer"
                },
                "category": {"type": "keyword"},
                "url": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 위키 인덱스 설정
    wiki_index = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "nori_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "analyzer": "nori_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "category": {"type": "keyword"},
                "preview": {
                    "type": "text",
                    "analyzer": "nori_analyzer"
                },
                "content": {
                    "type": "text",
                    "analyzer": "nori_analyzer"
                },
                "type": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    # 인덱스 생성
    if not es.indices.exists(index="news"):
        es.indices.create(index="news", body=news_index)
        print("✅ 뉴스 인덱스 생성 완료")
    
    if not es.indices.exists(index="wiki"):
        es.indices.create(index="wiki", body=wiki_index)
        print("✅ 위키 인덱스 생성 완료")

def index_news(news_item):
    """뉴스를 Elasticsearch에 인덱싱"""
    es = get_es_client()
    doc = {
        "id": news_item.id,
        "title": news_item.title,
        "source": news_item.source,
        "date": news_item.date,
        "summary": news_item.summary or "",
        "category": news_item.category,
        "url": news_item.url,
        "created_at": news_item.created_at
    }
    es.index(index="news", id=news_item.id, document=doc)

def index_wiki(wiki_item):
    """위키를 Elasticsearch에 인덱싱"""
    es = get_es_client()
    doc = {
        "id": wiki_item.id,
        "title": wiki_item.title,
        "category": wiki_item.category,
        "preview": wiki_item.preview or "",
        "content": wiki_item.content or "",
        "type": wiki_item.type,
        "created_at": wiki_item.created_at
    }
    es.index(index="wiki", id=wiki_item.id, document=doc)

def search_all(query, size=20):
    """뉴스와 위키 통합 검색"""
    es = get_es_client()
    
    # 뉴스 검색
    news_query = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "summary"],
                "type": "best_fields"
            }
        },
        "size": size
    }
    news_results = es.search(index="news", body=news_query)
    
    # 위키 검색
    wiki_query = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "preview", "content"],
                "type": "best_fields"
            }
        },
        "size": size
    }
    wiki_results = es.search(index="wiki", body=wiki_query)
    
    return {
        "news": [hit["_source"] for hit in news_results["hits"]["hits"]],
        "wiki": [hit["_source"] for hit in wiki_results["hits"]["hits"]]
    }
