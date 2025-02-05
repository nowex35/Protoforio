from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from database import get_db
from models import Topic, Language
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import MeCab
from pydantic import BaseModel

class submit_data(BaseModel):
    freetext: str
    engineerType: str
    programmingLanguage: str
    technologyPreference: str
    interestFields: str

app = FastAPI()

def tokenize(text: str) -> str:
    """テキストを形態素解析して、スペース区切りのトークンに変換する関数。"""
    tagger = MeCab.Tagger("-Owakati")
    return tagger.parse(text).strip()

topics_with_descriptions: dict[str, str] = {
    "todo list": "タスクや予定を管理するためのアプリ。",
    "chat app": "リアルタイムでメッセージのやり取りができるアプリ。",
    "map app": "地図を表示し、目的地までのルート案内を提供するアプリ。",
    "weather app": "天気予報を確認できるアプリ。",
    "music app": "音楽を再生・管理するためのアプリ。",
    "news app": "最新のニュース記事を閲覧できるアプリ。",
    "memo app": "簡単なメモを取るためのアプリ。",
    "calendar app": "スケジュールを管理するためのアプリ。",
    "photo app": "写真を撮影・編集・管理するアプリ。",
    "video app": "動画を撮影・編集・管理するアプリ。",
    "game app": "ゲームをプレイするためのアプリ。",
    "health app": "健康管理や運動の記録をサポートするアプリ。",
    "shopping app": "オンラインで商品を検索・購入できるアプリ。",
    "food app": "レシピ検索や飲食店の情報を提供するアプリ。",
    "travel app": "旅行の計画や観光情報を提供するアプリ。",
    "study app": "学習をサポートするアプリ。",
    "work app": "仕事の管理や生産性向上をサポートするアプリ。",
    "finance app": "収支管理や投資情報を提供するアプリ。",
    "social app": "SNSやコミュニティ機能を提供するアプリ。",
    "dating app": "恋愛・出会いを目的としたアプリ。",
    "job app": "求人情報を検索・応募できるアプリ。",
    "hobby app": "趣味を楽しむためのアプリ。",
    "pet app": "ペットの管理や情報を共有するアプリ。",
    "home app": "家の管理やスマートホーム機能を提供するアプリ。",
    "car app": "車の管理やナビ機能を提供するアプリ。",
    "plant app": "植物の管理や育成をサポートするアプリ。",
    "fashion app": "ファッション情報を提供するアプリ。",
    "beauty app": "美容情報やスキンケア管理をサポートするアプリ。",
    "sports app": "スポーツの記録や情報を提供するアプリ。",
    "entertainment app": "映画・音楽・イベント情報を提供するアプリ。",
    "learning app": "知識習得を目的としたアプリ。",
    "religion app": "宗教に関する情報やコミュニティ機能を提供するアプリ。",
    "charity app": "寄付やボランティア活動を支援するアプリ。",
    "community app": "同じ関心を持つ人々と交流できるアプリ。",
    "other app": "その他の目的で使用されるアプリ。"
}


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/recommend")
def recommend():
    topic, description = random.choice(list(topics_with_descriptions.items()))
    return {"topic": topic, "description": description}

@app.get("/random_topic")
def random_topic(db: Session = Depends(get_db)):
    topic = db.execute(select(Topic).order_by(func.random()).limit(1)).scalar()
    if topic:
        return {"id": topic.id, "name": topic.name, "description": topic.description}
    return {"message": "No topic found."}

@app.get("/topics")
def get_all_topics(db: Session = Depends(get_db)):
    topics = topics = db.execute(select(Topic)).scalars().all()
    return topics

@app.get("/language")
def random_language(db: Session = Depends(get_db)):
    language = db.execute(select(Language).order_by(func.random()).limit(1)).scalar()
    if language:
        return {"name": language.name, "is_modern": language.is_modern, "is_popular": language.is_popular}
    return {"language": language}

@app.get("/answer")
def answer(db: Session = Depends(get_db)):
    topic = db.execute(select(Topic).order_by(func.random()).limit(1)).scalar()
    language = db.execute(select(Language).order_by(func.random()).limit(1)).scalar()
    if language and topic:
        return {"answer": f"{topic.name} を {language.name}でつくる"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/corresponding_answer")
def corresponding_answer(db: Session = Depends(get_db), topic_txt: str = ""):
    try:
        if not topic_txt.strip():
            return {"message": "Please provide a valid topic text."}

        # 入力テキストを形態素解析
        topic_txt_processed = tokenize(topic_txt)

        # DBからデータを取得
        topics = db.execute(select(Topic)).scalars().all()
        language = db.execute(select(Language).order_by(func.random()).limit(1)).scalar()

        if not topics:
            return {"message": "No topic available."}

        # TF-IDF ベクトル化
        vectorizer = TfidfVectorizer()
        # 形態素解析を適用して、分かち書きされたトピックの文字列リスト
        topic_descriptions = [tokenize(topic.description) for topic in topics]
        tfidf_matrix = vectorizer.fit_transform(topic_descriptions)

        # 入力テキストを同じベクトル空間にマッピング（変換）
        topic_text_vector = vectorizer.transform([topic_txt_processed])

        # コサイン類似度を計算
        similarities = cosine_similarity(topic_text_vector, tfidf_matrix).flatten()

        # 例外処理: すべての類似度が 0 の場合
        if similarities.max() == 0:
            return {"message": "No relevant topic found."}

        # 最も類似度が高いトピックを取得
        top_index = similarities.argmax()
        recommendation = topics[top_index]

        if language and recommendation:
            return {"answer": f"{recommendation.name} を {language.name} でつくる"}

        return {"message": "No corresponding answer found."}

    except Exception as e:
        return {"message": "Internal server error"}
    

@app.post("/submit")
def recommend(data: submit_data,db: Session = Depends(get_db),):
    try:
        if not data.freetext.strip():
            return {"message": "Please provide a valid freetext."}
        
        tech_pref = data.technologyPreference
        
        # 入力テキストを形態素解析
        freetext_processed = tokenize(data.freetext)
        
        topics = db.execute(select(Topic)).scalars().all()
        
        # TF-IDF ベクトル化
        vectorizer = TfidfVectorizer()
        
        # 形態素解析を適用して、分かち書きされたトピックの文字列リスト
        topic_descriptions = [tokenize(topic.description) for topic in topics]
        tfidf_matrix = vectorizer.fit_transform(topic_descriptions)
        
        # 入力テキストを同じベクトル空間にマッピング（変換）
        freetext_vector = vectorizer.transform([freetext_processed])
        
        # コサイン類似度を計算
        similarities = cosine_similarity(freetext_vector, tfidf_matrix).flatten()
        
        # 例外処理: すべての類似度が 0 の場合
        if similarities.max() == 0:
            return {"message": "No relevant topic found."}
        
        # 最も類似度が高いトピックを取得
        top_index = similarities.argmax()
        recommendation = topics[top_index]
        
        if recommendation and data.programmingLanguage== "" and tech_pref== "modern":
            language = db.execute(select(Language).filter(Language.is_modern == True)).scalar()
            return {"answer": f"{recommendation.name} を {language.name} でつくる"}
        elif recommendation and data.programmingLanguage== "" and tech_pref== "legacy":
            language = db.execute(select(Language).filter(Language.is_modern == False)).scalar()
            return {"answer": f"{recommendation.name} を {language.name} でつくる"}
        else:
            return {"answer": f"{recommendation.name} を {data.programmingLanguage} でつくる"}
    except:
        return {"message": "Internal server error"}