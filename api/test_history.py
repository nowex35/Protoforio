from fastapi.testclient import TestClient
from main import app, get_db
from uuid import uuid4

client = TestClient(app)

# FakeQuery クラスで filter, order_by, all のメソッドチェーンを実装
class FakeQuery:
    def __init__(self, fake_user_id):
        self.fake_user_id = fake_user_id

    def filter(self, *args):
        # 実際のフィルタ条件は無視しているが、メソッドチェーンは継続
        return self

    def order_by(self, *args):
        # 順序指定は無視するが、チェーンの継続
        return self

    def all(self):
        return [
            {
                "id": str(uuid4()),
                "user_id": self.fake_user_id,
                "recommendation": {"title": "Test Title", "description": "Test desc"},
                "created_at": "2025-02-25T09:14:12.499801"
            }
        ]

# FakeSession クラスで query メソッドが FakeQuery を返すように実装
class FakeSession:
    def __init__(self, fake_user_id):
        self.fake_user_id = fake_user_id

    def query(self, model):
        return FakeQuery(self.fake_user_id)

def test_get_user_history(monkeypatch):
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    fake_user_id = str(uuid4())
    app.dependency_overrides[get_db] = lambda: FakeSession(fake_user_id)

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

    monkeypatch.setattr("requests.get", mock_get)

    headers = {
        "Authorization": "Bearer valid_token"
    }
    response = client.get("/history", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) > 0
    assert "title" in data["history"][0]["recommendation"]
    assert data["history"][0]["recommendation"]["title"] == "Test Title"

def test_get_user_history_no_token(monkeypatch):
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    app.dependency_overrides[get_db] = lambda: FakeSession("")

    response = client.get("/history")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Authorization header is missing."

def test_get_user_history_invalid_token(monkeypatch):
    monkeypatch.setenv("AUTH_URL", "http://mock-auth-url")
    app.dependency_overrides[get_db] = lambda: FakeSession("")

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

    headers = {
        "Authorization": "Bearer invalid_token"
    }
    response = client.get("/history", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid access token"

# テスト終了後、依存関係のオーバーライドをクリア
def teardown_module(module):
    app.dependency_overrides = {}