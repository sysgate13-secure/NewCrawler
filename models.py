from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base

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
    preview = Column(Text)
    content = Column(Text)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.now)
