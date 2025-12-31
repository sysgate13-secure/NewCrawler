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
    
    news_index = {
        "settings": {"analysis": {"analyzer": {"nori_analyzer": {"type": "custom", "tokenizer": "nori_tokenizer", "filter": ["lowercase"]}}}},
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "analyzer": "nori_analyzer", "fields": {"keyword": {"type": "keyword"}}},
                "source": {"type": "keyword"},
                "date": {"type": "date", "format": "yyyy-MM-dd"},
                "summary": {"type": "text", "analyzer": "nori_analyzer"},
                "category": {"type": "keyword"},
                "url": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    wiki_index = {
        "settings": {"analysis": {"analyzer": {"nori_analyzer": {"type": "custom", "tokenizer": "nori_tokenizer", "filter": ["lowercase"]}}}},
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "analyzer": "nori_analyzer", "fields": {"keyword": {"type": "keyword"}}},
                "category": {"type": "keyword"},
                "preview": {"type": "text", "analyzer": "nori_analyzer"},
                "content": {"type": "text", "analyzer": "nori_analyzer"},
                "type": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
    }
    
    if not es.indices.exists(index="news"):
        es.indices.create(index="news", body=news_index)
    if not es.indices.exists(index="wiki"):
        es.indices.create(index="wiki", body=wiki_index)

def index_news(news_item):
    es = get_es_client()
    doc = {
        "id": news_item.id, "title": news_item.title, "source": news_item.source,
        "date": news_item.date, "summary": news_item.summary or "", "category": news_item.category,
        "url": news_item.url, "created_at": news_item.created_at
    }
    es.index(index="news", id=news_item.id, document=doc)

def index_wiki(wiki_item):
    es = get_es_client()
    doc = {
        "id": wiki_item.id, "title": wiki_item.title, "category": wiki_item.category,
        "preview": wiki_item.preview or "", "content": wiki_item.content or "",
        "type": wiki_item.type, "tags": [tag.strip() for tag in (wiki_item.tags or "").split(",") if tag.strip()],
        "created_at": wiki_item.created_at
    }
    es.index(index="wiki", id=wiki_item.id, document=doc)

def _build_query_dsl(query, fields, category, page, limit):
    """검색어, 필터, 페이지네이션을 포함한 Elasticsearch DSL을 생성합니다."""
    if query:
        base_query = {"multi_match": {"query": query, "fields": fields, "type": "best_fields"}}
    else:
        base_query = {"match_all": {}}

    must_clauses = [base_query]
    if category:
         must_clauses.append({"term": {"category": category}})

    return {
        "query": {"bool": {"must": must_clauses}},
        "from": (page - 1) * limit,
        "size": limit,
        "track_total_hits": True
    }

def search_news(query, page=1, limit=20, category=None):
    """뉴스 인덱스만 검색합니다."""
    es = get_es_client()
    dsl = _build_query_dsl(query, ["title^3", "summary"], category, page, limit)
    results = es.search(index="news", body=dsl)
    
    return {
        "results": [hit["_source"] for hit in results["hits"]["hits"]],
        "total": results["hits"]["total"]["value"]
    }

def search_wiki(query, page=1, limit=20, category=None):
    """위키 인덱스만 검색합니다."""
    es = get_es_client()
    dsl = _build_query_dsl(query, ["title^3", "preview", "content", "tags"], category, page, limit)
    results = es.search(index="wiki", body=dsl)
    
    return {
        "results": [hit["_source"] for hit in results["hits"]["hits"]],
        "total": results["hits"]["total"]["value"]
    }

def search_all(query, page=1, limit=20, category=None):
    """뉴스와 위키 통합 검색 (msearch를 사용하여 단일 요청으로 최적화)"""
    es = get_es_client()
    
    # 뉴스 검색 DSL
    news_dsl = _build_query_dsl(query, ["title^3", "summary"], category, page, limit)
    
    # 위키 검색 DSL
    wiki_dsl = _build_query_dsl(query, ["title^3", "preview", "content", "tags"], category, page, limit)

    # msearch 요청 생성
    request_body = []
    request_body.append({"index": "news"})
    request_body.append(news_dsl)
    request_body.append({"index": "wiki"})
    request_body.append(wiki_dsl)
    
    responses = es.msearch(body=request_body)
    
    news_results = responses['responses'][0]
    wiki_results = responses['responses'][1]
    
    return {
        "news": [hit["_source"] for hit in news_results["hits"]["hits"]],
        "news_total": news_results["hits"]["total"]["value"],
        "wiki": [hit["_source"] for hit in wiki_results["hits"]["hits"]],
        "wiki_total": wiki_results["hits"]["total"]["value"],
    }