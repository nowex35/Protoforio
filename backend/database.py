import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# Cloud SQL の接続 URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 同期エンジンの作成
engine = create_engine(DATABASE_URL, echo=True)

# セッションの作成
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# DBセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()