# test_recommendations.py

from fastapi.testclient import TestClient
from main import app, get_db
from uuid import uuid4, UUID
import jwt
import os

client = TestClient(app)

# --- Fake モデル・セッションの定義 ---

# RecommendationModel の代替オブジェクト（実際は ORM オブジェクトですが、ここでは属性で再現）
class FakeRecommendation:
    def __init__(self, rec_id, user_id, recommendation):
        self.id = rec_id
        self.user_id = user_id  # UUID 型で扱う
        self.recommendation = recommendation

# メソッドチェーンを再現する FakeQuery クラス
class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args):
        # 実際のフィルタ条件はチェックせず、チェーン継続のため自身を返す
        return self

    def order_by(self, *args):
        # 順序指定は無視するが、チェーンの継続のため自身を返す
        return self

    def first(self):
        return self.result

# 正常系用 FakeSession：クエリで FakeRecommendation オブジェクトを返す
class FakeSessionValid:
    def __init__(self, recommendation_obj):
        self.recommendation_obj = recommendation_obj

    def query(self, model):
        return FakeQuery(self.recommendation_obj)

# リソースが見つからない場合用 FakeSession：first() で None を返す
class FakeSessionNotFound:
    def query(self, model):
        return FakeQuery(None)

# アクセス権エラー用 FakeSession：トークンユーザーと異なる所有者のレコメンデーションを返す
class FakeSessionForbidden:
    def __init__(self, recommendation_obj):
        self.recommendation_obj = recommendation_obj

    def query(self, model):
        return FakeQuery(self.recommendation_obj)

# --- ヘルパー関数 ---

def generate_token(user_id, secret="test_secret"):
    """指定の user_id を含む JWT トークンを生成する"""
    return jwt.encode({"userId": user_id}, secret)

def override_get_db_factory(fake_session):
    """get_db の依存関係オーバーライド用のファクトリ"""
    return lambda: fake_session

# --- テストケース ---

def test_get_recommendation_detail_valid(monkeypatch):
    """
    正常系テスト:
    ・トークンが有効で、リクエストユーザーとレコメンデーション所有者が一致する場合、
      レコメンデーションの内容（JSON）が返る
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    fake_user_id = str(uuid4())
    token = generate_token(fake_user_id)
    rec_id = str(uuid4())
    recommendation_data = {"title": "Valid Title", "description": "Valid description"}
    # FakeRecommendation の user_id は UUID 型に変換
    fake_recommendation = FakeRecommendation(rec_id, UUID(fake_user_id), recommendation_data)

    # FastAPI の依存関係オーバーライドで FakeSessionValid を使用
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionValid(fake_recommendation))

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # レスポンスが正しい recommendation データであることを検証
    assert data == recommendation_data

def test_get_recommendation_detail_no_auth(monkeypatch):
    """
    認証エラー:
    Authorization ヘッダーが存在しない場合、401 エラーが返る
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    rec_id = str(uuid4())
    # DB 呼び出しが実行されないケースですが、依存関係オーバーライドを設定しておく
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionValid(None))
    response = client.get(f"/recommendations/{rec_id}")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Authorization header is missing."

def test_get_recommendation_detail_not_found(monkeypatch):
    """
    リソース未検出:
    有効なトークンだが、DB クエリでレコメンデーションが見つからない場合、404 エラーが返る
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    fake_user_id = str(uuid4())
    token = generate_token(fake_user_id)
    rec_id = str(uuid4())
    # FakeSessionNotFound で first() が None を返す
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionNotFound())
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Recommendation not found"

def test_get_recommendation_detail_forbidden(monkeypatch):
    """
    アクセス権エラー:
    トークンのユーザーと、レコメンデーションの所有者が異なる場合、403 エラーが返る
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    token_user_id = str(uuid4())
    token = generate_token(token_user_id)
    rec_id = str(uuid4())
    # レコメンデーションの所有者は別のユーザー
    other_user_id = str(uuid4())
    recommendation_data = {"title": "Forbidden Title", "description": "Forbidden description"}
    fake_recommendation = FakeRecommendation(rec_id, UUID(other_user_id), recommendation_data)
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionForbidden(fake_recommendation))

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Forbidden: You do not have access to this recommendation."

def test_get_recommendation_detail_invalid_token(monkeypatch):
    """
    不正なトークン:
    トークンがデコードできない場合、例外が発生し 500 エラーとして返される
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    rec_id = str(uuid4())
    # トークンが無効なため、FakeSession は使用されるが処理されない
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionValid(None))
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    # この場合、jwt.decode で例外が発生し 500 エラーになる
    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]

# テスト終了後、依存関係のオーバーライドをクリア
def teardown_module(module):
    app.dependency_overrides = {}
