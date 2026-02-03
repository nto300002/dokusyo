## 「コードで聞かれやすい」部分ランキング

| 優先度 | 機能 | 理由 |
|--------|------|------|
| ⭐⭐⭐ | **JWT認証** | 構成図に大きく書いてある。セキュリティの話をしているので必ず深掘りされる |
| ⭐⭐⭐ | **Pydanticバリデーション** | スライドで「不正なデータを弾く」と言っている |
| ⭐⭐ | Google Calendar API連携 | 外部API連携の代表例 |
| ⭐⭐ | Stripe Webhook | 決済処理の仕組み |

---

## 最優先：JWT認証

**なぜ最も聞かれやすいか**：
- 構成図に「JWT」「CORS」と明記している
- 「セキュリティを重視した」と言っている
- 認証はWebアプリの基本中の基本

---

### 想定される質問

| 質問 | 答えられる必要がある |
|------|---------------------|
| JWTの仕組みを説明してください | トークンの構造（Header.Payload.Signature） |
| トークンの有効期限はどう設定していますか？ | アクセストークン：15分〜1時間、リフレッシュトークン：7日など |
| トークンはどこに保存していますか？ | HttpOnly Cookie / localStorage の選択理由 |
| リフレッシュトークンは実装していますか？ | はい/いいえ と理由 |

---

### コードの基本パターン（FastAPI + JWT）

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# トークン生成
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# トークン検証
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    return user_id
```

---

### 面接での回答例

> 「JWT認証は、python-joseライブラリを使って実装しています。
>
> トークン生成時に、ペイロードにユーザーIDと有効期限を含めて、HS256アルゴリズムで署名しています。
>
> 有効期限はアクセストークンが30分、リフレッシュトークンが7日に設定しています。
>
> トークンの保存先は、XSS対策としてHttpOnly Cookieに保存しています。localStorageだとJavaScriptから読み取れてしまうためです。」

---

JWT認証の練習をしますか？それとも他の項目（Pydantic等）を先に確認しますか？