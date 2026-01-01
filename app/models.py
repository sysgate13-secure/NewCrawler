from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.database import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    date = Column(String, nullable=False)
    summary = Column(Text)
    category = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Wiki(Base):
    __tablename__ = "wiki"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    tags = Column(String, nullable=True)
    preview = Column(Text)
    content = Column(Text)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class CrawlLog(Base):
    __tablename__ = "crawl_log"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)  # 'success', 'failed', 'running'
    count = Column(Integer, default=0)
    message = Column(Text)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

class CrawlSource(Base):
    __tablename__ = "crawl_source"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 소스 이름 (예: "보안뉴스", "HackRead")
    url = Column(String, nullable=False)  # 크롤링할 URL
    country = Column(String, nullable=False)  # 'kr' 또는 'en'
    description = Column(Text)  # 소스 설명
    selector_config = Column(Text)  # JSON 형태의 셀렉터 설정
    is_active = Column(Boolean, default=True)  # 활성화 여부
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
