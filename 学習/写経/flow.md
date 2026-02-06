面接練習から切り替えですね。学習リソースと写経のコメント術についてまとめます。

---

## 公式学習リソース

### Django
- **公式チュートリアル**: https://docs.djangoproject.com/en/5.1/intro/tutorial01/
  - 投票アプリを7パートで構築。ORM・View・Template・Testまでカバー
- **GitHub写経向け**: [djangoproject.com](https://github.com/django/djangoproject.com)（Django公式サイト自体のソースコード）

### FastAPI
- **公式チュートリアル**: https://fastapi.tiangolo.com/tutorial/
- **GitHub写経向け**: [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
  - FastAPI + SQLAlchemy + Alembic の実践的テンプレート

### Next.js
- **公式Learn**: https://nextjs.org/learn
  - App Router、Server Components、データフェッチまで段階的に学べる
- **GitHub写経向け**: [next.js/examples](https://github.com/vercel/next.js/tree/canary/examples)

### React
- **公式ドキュメント**: https://react.dev/learn
- **GitHub写経向け**: [react.dev](https://github.com/reactjs/react.dev) のチュートリアルコード

### AWS
- **公式ハンズオン**: https://aws.amazon.com/getting-started/hands-on/
- **GitHub写経向け**: [aws-samples](https://github.com/aws-samples)
  - SES例: `aws-samples/amazon-ses-*`

---

## 写経で学習効果を上げるコメントの付け方

### ❌ 効果の低いコメント

```python
# ユーザーを取得する
user = db.query(User).filter(User.id == user_id).first()
```

→ **コードを日本語に訳しただけ**。読めば分かるので学びがない。

---

### ✅ 効果の高いコメント（3つの型）

#### 型1：「なぜ」を書く（Why型）

```python
# firstで1件だけ取得する → allだと不要なメモリ消費が発生するため
user = db.query(User).filter(User.id == user_id).first()
```

#### 型2：「比較」を書く（Compare型）

```python
# Django ORMなら: User.objects.get(id=user_id)
# SQLAlchemyはクエリビルダ式 → より柔軟だが記述が長い
user = db.query(User).filter(User.id == user_id).first()
```

#### 型3：「応用」を書く（Apply型）

```python
# けいかくんに適用するなら: 利用者IDで支援計画を取得する場面に使える
# plan = db.query(SupportPlan).filter(SupportPlan.user_id == user_id).first()
user = db.query(User).filter(User.id == user_id).first()
```

---

### コメントテンプレート

```python
# [What]  何をしている: ○○を取得
# [Why]   なぜこの方法: ○○だから / ○○と比較して
# [Apply] 自分のプロジェクトでは: ○○に使える
# [Q]     疑問: ○○の場合はどうなる？→ 後で調べる
```

### 実践例（Djangoチュートリアル写経）

```python
# [What]  Questionモデルの定義
# [Why]   Django ORMはActive Record → モデル定義=テーブル定義になる
#         SQLAlchemyだとBase + Column()で定義するが、Djangoはmodels.Modelを継承するだけ
# [Apply] けいかくんのSupportPlanモデルと同じ役割
# [Q]     ForeignKeyのon_deleteはDjangoだとモデル側で定義？SQLAlchemyはDB側で定義していた
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
```

---

### 学習サイクル

```
① 写経（コメント付き）
② 疑問を [Q] タグで記録
③ 公式ドキュメント or AIで解消
④ けいかくんとの差分を [Apply] で記録
⑤ 週末に [Apply] をまとめてブログ or Notionに整理
```

---

面接練習に戻りますか？スケーラビリティの質問がまだ残っています。