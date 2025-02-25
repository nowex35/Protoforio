from fastapi.testclient import TestClient
from main import app, get_db
from uuid import uuid4
import jwt

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
    # テスト用シークレットの設定
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")

    # モックデータを作成
    fake_user_id = str(uuid4())
    secret = "test_secret"
    token = jwt.encode({"userId": fake_user_id}, secret)
    
    # FastAPI の依存関係オーバーライドを利用して FakeSession を返すようにする
    app.dependency_overrides[get_db] = lambda: FakeSession(fake_user_id)

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = client.get("/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    # FakeSession で作成したデータが返るので、リストの長さは 1 となるはず
    assert len(data["history"]) > 0
    assert "title" in data["history"][0]["recommendation"]
    assert data["history"][0]["recommendation"]["title"] == "Test Title"

def test_get_user_history_no_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    # DB の呼び出しを防ぐために、FakeSession を利用（空のリストを返す）
    class EmptyFakeSession:
        def query(self, model):
            return FakeQuery(fake_user_id="")  # 空のユーザーIDでも OK
    app.dependency_overrides[get_db] = lambda: EmptyFakeSession()

    response = client.get("/history")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Authorization header is missing."

def test_get_user_history_invalid_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    # DB の呼び出しを防ぐために、FakeSession を利用（今回は実際は使われない）
    class EmptyFakeSession:
        def query(self, model):
            return FakeQuery(fake_user_id="") 
    app.dependency_overrides[get_db] = lambda: EmptyFakeSession()

    headers = {
        "Authorization": "Bearer invalid_token"
    }
    response = client.get("/history", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid token."
