from sqlalchemy import Column, Integer, String, Text
from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    content = Column(Text)

