from fastapi import FastAPI, Depends, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel, UUID4
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from sqlalchemy.orm import Session
from database import get_db
from models import RecommendationModel
from os import getenv
from uuid import UUID
"""
from transformers import AutoTokenizer, AutoModel
import torch
import random
import MeCab
from models import Topic , Languages, LanguageFeatures
from sqlalchemy import select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

"""
load_dotenv()
origins = [
    "http://localhost:3000",  # フロントエンドのオリジン (例)
    "https://127.0.0.1:3000"  # フロントエンドのオリジン (例)
]

# model_name = 'cl-tohoku/bert-base-japanese-v2'
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)

class submit_data(BaseModel):
    engineerType: str
    programmingLanguage: str
    learningPreference: str
    interestFields: List[str]
    accessToken: Optional[str] = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/submit_deepseek")
def recommend_deepseek(data: submit_data,db: Session = Depends(get_db)):
    print(f"data:{data}")
    single_string = (
        "以下の内容に関して、日本語でJSON形式で答えてください。"
        "出力フォーマットは以下のようにしてください:"
        '{"title": "string", "description": "string", "roadmap": ["string"], "technologies": ["string"], "outcomes": ["string"]}.'
        f"使いたい言語: {data.programmingLanguage}, "
        f"エンジニアのタイプ: {data.engineerType}, "
        f"興味のある分野: {', '.join(data.interestFields)}, "
        f"作品の難易度: {data.learningPreference} "
        "出力してもらいたい内容は初心者がエンジニアとしてのポートフォリオを作成する際のお題を作ってほしいです.単一のアイデアを出してください。また学習ロードマップに関して、初心者がわからない用語は使わないでください"
        "必ず、```jsonと```で囲んでjsonだけを出力してください。"
    )
    
    response = requests.post(f"{getenv("DEEPSEEK_URL")}:8000/response", json={"text": single_string})
    if response.status_code != 200:
        return {
            "error": f"Failed to fetch from DeepSeek API. Status Code: {response.status_code}",
            "details": response.text
        }
    
    response_json = response.json()
    # DeepSeek のレスポンスは {"response": "全体のテキスト..."} の形式を想定
    raw_text = response_json.get("response", "")
    
    if "```json" in raw_text:
        # 想定通り返ってきた場合
        json_text = raw_text.split("```json")[2].split("```", 1)[0].strip()
    else:
        # ないの場合、直接JSONとして解析
        json_text = raw_text.split("</think>")[1].strip()
        json_text = json_text.strip()
    if json_text:
        parsed_data = json.loads(json_text)
    else:
        raise ValueError("Failed to parse JSON response from DeepSeek API.")
    if data.accessToken:
        me_response = requests.get(f"{getenv('AUTH_URL')}/auth/me", headers={"Authorization": f"Bearer {data.accessToken}"})
        if me_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid access token")
        me_response_data = me_response.json()
        user_id = me_response_data.get('user',{}).get("userId")
        uuid_user_id = UUID(user_id)
        if uuid_user_id:
            db_rec = RecommendationModel(user_id=uuid_user_id, recommendation=parsed_data)
            db.add(db_rec)
            db.commit()
            db.refresh(db_rec)
        return parsed_data
    else:
        return parsed_data

@app.get("/history")
def get_user_history(request: Request, db: Session = Depends(get_db)):
    """
    特定のユーザーのレコメンド履歴を取得
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing.")
        accessToken = auth_header.split(" ")[1]
        response = requests.get(f"{getenv('AUTH_URL')}/auth/me", headers={"Authorization": f"Bearer {accessToken}"})
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid access token")
        me_response_data = response.json()
        user_id = me_response_data.get('user',{}).get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid access token")
        history = (
            db.query(RecommendationModel).
            filter(RecommendationModel.user_id == user_id).
            order_by(RecommendationModel.created_at.desc()).
            all()
        )
        return {"history":history}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/recommendations/{rec_id}")
def get_recommendation_detail(request: Request, rec_id: UUID4, db: Session = Depends(get_db)):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing.")
        accessToken = auth_header.split(" ")[1]
        me_response = requests.get(f"{getenv('AUTH_URL')}/auth/me", headers={"Authorization": f"Bearer {accessToken}"})
        if me_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid access token")
        me_response_data = me_response.json()
        user_id = me_response_data.get('user',{}).get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid access token")
        rec = db.query(RecommendationModel).filter(RecommendationModel.id == rec_id).first()
        if rec is None:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        if rec.user_id != UUID(user_id):
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this recommendation.")
        return rec.recommendation
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

"""
@app.post("/submit_gemini")
def recommend_gemini(data: submit_data, user_id: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        API_KEY = os.getenv("GEMINI_API_KEY")
        if not API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }

        # Gemini API へリクエストするデータ
        input_data = {
            "contents": [{
                "parts": [{
                    "text": (
                        "以下の内容に関して、日本語でJSON形式で答えてください。"
                        "出力フォーマットは以下のようにしてください:"
                        '{"title": "string", "description": "string", "roadmap": ["string"], "technologies": ["string"], "outcomes": ["string"]}.'
                        f"使いたい言語: {data.programmingLanguage}, "
                        f"エンジニアのタイプ: {data.engineerType}, "
                        f"興味のある分野: {', '.join(data.interestFields)}"
                        f"作品の難易度: {data.learningPreference}"
                        "出力してもらいたい内容は初心者がエンジニアとしてのポートフォリオを作成する際のお題を作ってほしいです.単一のアイデアを出してください。また学習ロードマップに関して、初心者がわからない用語は使わないでください"
                    )
                }]
            }]
        }

        response = requests.post(url, headers=headers, json=input_data)

        if response.status_code != 200:
            return {"error": f"Failed to fetch from Gemini API. Status Code: {response.status_code}", "details": response.text}

        response_json = response.json()

        # Gemini API のレスポンスからテキストを取得
        raw_text = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        # ` ```json ` のマークダウンを削除
        cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()

        print(f"Cleaned Text: {cleaned_text}")

        try:
            parsed_data = json.loads(cleaned_text)  # JSON をパース
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse JSON response from Gemini API.")
        
        if (user_id):
            db_rec = RecommendationModel(user_id=user_id, recommendation=parsed_data)
            db.add(db_rec)
            db.commit()
            db.refresh(db_rec)

        return parsed_data  # フロントエンドが処理しやすい形で返す

    except Exception as e:
        print("Error occurred:")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def tokenize(text: str) -> str:
    #テキストを形態素解析して、スペース区切りのトークンに変換する関数
    tagger = MeCab.Tagger("-Owakati")
    return tagger.parse(text).strip()

def embed_text(text: str):
    inputs = tokenizer(text, return_tensors="pt",padding=True,truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

def find_most_similar_topic(interest_fields: List[str], topics: List[Topic]):
    #興味のある分野と最も類似するトピックをBERTベースの類似度で検索
    if not topics:
        return None
    
    topic_texts = [tokenize(f"{t.name} {t.description}") for t in topics]
    topic_vectors = np.array([embed_text(text) for text in topic_texts])
    
    interest_text = " ".join(interest_fields)
    query_vector = embed_text(interest_text)
    
    '''
    ＜類似度の計算＞
    ・以下は疎行列の計算では速いが、全てのベクトル間でペアワイズ比較を計算し、またすべてのベクトル正規化を行うため、計算量が多く時間がかかる。
    similarities = cosine_similarity([query_vector], topic_vectors).flatten()
    '''
    similarities = np.dot(topic_vectors, query_vector) / (np.linalg.norm(topic_vectors, axis=1) * np.linalg.norm(query_vector))
    
    #最も類似するトピックを返す
    if similarities.max() == 0:
        return random.choice(topics)
    else:
        top_n = 3
        top_indices = np.argsort(similarities)[::-1][:top_n]
        chosen_index = random.choice(top_indices)  # 1つだけ選ぶ
        return topics[chosen_index]  # そのインデックスのトピックを返す


TF-IDFとコサイン類似度を使ってDBの保存されたお題との一致度により提案するAPI

@app.post("/submit")
def recommend(data: submit_data, db: Session = Depends(get_db)):
    print(data)
    try:

        tech_pref = data.learningPreference  # 学習の好み
        interest_fields = data.interestFields  # 興味のある分野
        topics = db.execute(select(Topic)).scalars().all()
        language_features = db.execute(select(LanguageFeatures)).scalars().all()

        if not topics:
            return {"message": "No topics available."}

        # 形態素解析を適用したトピックの説明リスト
        topic_descriptions = [tokenize(topic.description) for topic in topics]

        # TF-IDF ベクトル化
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(topic_descriptions)

        # 入力テキストを同じベクトル空間に変換

        # 興味のある分野を文字列に変換
        interest_text = " ".join(interest_fields)  # リスト → 文字列

        # 入力テキストを TF-IDF ベクトル空間に変換
        input_vector = vectorizer.transform([interest_text])

        # コサイン類似度を計算
        similarities = cosine_similarity(input_vector, tfidf_matrix).flatten()


        # 類似度がすべてゼロの場合
        if similarities.max() == 0:
            recommendation = random.choice(topics)  # ランダムにトピックを選択
        else:
            top_index = similarities.argmax()
            recommendation = topics[top_index]

        # 言語の決定
        if data.programmingLanguage == "わからない":
            if tech_pref == "modern":
                language = db.execute(select(language_features).filter(language_features.feature_id == 13)).scalars().all()
            elif tech_pref == "legacy":
                language = db.execute(select(language_features).filter(language_features.feature_id == 14)).scalars().all()
            else:
                language = db.execute(select(language_features)).scalars().all()
            chosen_language_id = random.choice(language)  # ランダムに選択
            chosen_language = db.execute(select(Languages).filter(Languages.id == chosen_language_id.language_id)).scalar()
        else:
            chosen_language = data.programmingLanguage

        return {"name": {recommendation.name},"language":chosen_language}

    except Exception as e:
        return {"message": f"Internal server error: {str(e)}"}
    

import traceback

BERTとすでに保存しているお題DBをつかって類似度をもとにお題を提案するAPI

@app.post("/submit_bert")
def recommend_bert(data: submit_data, db: Session = Depends(get_db)):
    try:
        print(f"Received Data: {data}")

        tech_pref = data.learningPreference
        interest_fields = data.interestFields

        topics = db.execute(select(Topic)).scalars().all()
        language_features = db.execute(select(LanguageFeatures)).scalars().all()

        if not topics:
            print("No topics found in the database")
            return {"message": "No topics available."}

        # 興味のある分野と最も類似するトピックを検索
        recommendation = find_most_similar_topic(interest_fields, topics)
        if not recommendation:
            print("No similar topic found")
            return {"message": "No matching topic found."}

        # 言語の決定
        if data.programmingLanguage == "わからない":
            if tech_pref == "modern":
                language = db.execute(select(LanguageFeatures).filter(LanguageFeatures.feature_id == 13)).scalars().all()
            elif tech_pref == "legacy":
                language = db.execute(select(LanguageFeatures).filter(LanguageFeatures.feature_id == 14)).scalars().all()
            else:
                language = db.execute(select(LanguageFeatures)).scalars().all()
            
            if not language:
                print("No matching language found")
                return {"message": "No matching language found."}

            chosen_language_id = random.choice(language)  # `language` が空ならエラー
            chosen_language = db.execute(select(Languages).filter(Languages.id == chosen_language_id.language_id)).scalar()
        else:
            chosen_language = data.programmingLanguage

        return {"name": recommendation.name, "language": chosen_language}

    except Exception as e:
        print("Error occurred:")
        traceback.print_exc()  # 例外の詳細を出力
        return {"message": f"Internal server error: {str(e)}"}
"""

