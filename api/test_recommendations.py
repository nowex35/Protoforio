from fastapi.testclient import TestClient
from main import app, get_db
from uuid import uuid4, UUID

client = TestClient(app)

from fastapi.testclient import TestClient
from main import app, get_db
from uuid import uuid4, UUID

client = TestClient(app)

# RecommendationModel の代替オブジェクト
class FakeRecommendation:
    def __init__(self, rec_id, user_id, recommendation):
        self.id = rec_id
        self.user_id = user_id  # UUID型で扱う
        self.recommendation = recommendation

# メソッドチェーンを再現するFakeQueryクラス
class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args):
        return self

    def first(self):
        return self.result

# 正常系用FakeSession
class FakeSessionValid:
    def __init__(self, recommendation_obj):
        self.recommendation_obj = recommendation_obj

    def query(self, model):
        return FakeQuery(self.recommendation_obj)

# 404エラー用FakeSession
class FakeSessionNotFound:
    def query(self, model):
        return FakeQuery(None)

# 403エラー用FakeSession
class FakeSessionForbidden:
    def __init__(self, recommendation_obj):
        self.recommendation_obj = recommendation_obj

    def query(self, model):
        return FakeQuery(self.recommendation_obj)

# DBファクトリーのオーバーライド用ヘルパー関数
def override_get_db_factory(fake_session):
    """get_dbの依存関係オーバーライド用のファクトリ"""
    return lambda: fake_session

def test_get_recommendation_detail_valid(monkeypatch):
    """
    正常系テスト:
    ・トークンが有効で、リクエストユーザーとレコメンデーション所有者が一致する場合、
      レコメンデーションの内容（JSON）が返る
    """
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    fake_user_id = str(uuid4())
    rec_id = str(uuid4())
    recommendation_data = {"title": "Valid Title", "description": "Valid description"}
    fake_recommendation = FakeRecommendation(rec_id, UUID(fake_user_id), recommendation_data)
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionValid(fake_recommendation))

    def mock_get(url, headers):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def get(self, key, default=None):
                return self.json_data.get(key, default)

        if url == "http://mock-auth-url/auth/me":  # パスを/auth/meに修正
            return MockResponse({"user":{"userId": fake_user_id}}, 200)
        return MockResponse(None, 404)

    monkeypatch.setattr("requests.get", mock_get)

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data == recommendation_data

def test_get_recommendation_detail_not_found(monkeypatch):
    """
    リソース未検出:
    有効なトークンだが、DB クエリでレコメンデーションが見つからない場合、404 エラーが返る
    """
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    fake_user_id = str(uuid4())
    rec_id = str(uuid4())
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionNotFound())

    def mock_get(url, headers):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def get(self, key, default=None):
                return self.json_data.get(key, default)

        if url == "http://mock-auth-url/auth/me":
            return MockResponse({"user": {"userId": fake_user_id}}, 200)
        return MockResponse(None, 404)

    monkeypatch.setattr("requests.get", mock_get)

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Recommendation not found"

def test_get_recommendation_detail_forbidden(monkeypatch):
    """
    アクセス権エラー:
    トークンのユーザーと、レコメンデーションの所有者が異なる場合、403 エラーが返る
    """
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    token_user_id = str(uuid4())
    rec_id = str(uuid4())
    other_user_id = str(uuid4())
    recommendation_data = {"title": "Forbidden Title", "description": "Forbidden description"}
    fake_recommendation = FakeRecommendation(rec_id, UUID(other_user_id), recommendation_data)
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionForbidden(fake_recommendation))

    def mock_get(url, headers):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def get(self, key, default=None):
                return self.json_data.get(key, default)

        if url == "http://mock-auth-url/auth/me":  # パスを/auth/meに修正
            return MockResponse({"user":{"userId": token_user_id}}, 200)
        return MockResponse(None, 404)

    monkeypatch.setattr("requests.get", mock_get)

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Forbidden: You do not have access to this recommendation."

def test_get_recommendation_detail_invalid_token(monkeypatch):
    """
    不正なトークン:
    トークンが無効な場合、401 エラーが返される
    """
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    rec_id = str(uuid4())
    app.dependency_overrides[get_db] = override_get_db_factory(FakeSessionValid(None))

    def mock_get(url, headers):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def get(self, key, default=None):
                return self.json_data.get(key, default)

        return MockResponse({"detail": "Invalid access token"}, 401)

    monkeypatch.setattr("requests.get", mock_get)

    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get(f"/recommendations/{rec_id}", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid access token"