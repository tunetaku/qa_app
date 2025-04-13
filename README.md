# QA アプリケーション

プラントエンジニアリング向けの質問回答管理システム

**※このアプリケーションはStreamlitを使用したプロトタイプです**

## 機能
- 質問の投稿・管理
- 回答の投稿・管理
- ベストアンサーの設定
- 解決済み/未解決のフィルタリング
- ユーザー管理

## セットアップ

1. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. データベースの初期化:
```bash
python db_init.py --init
```

3. ダミーデータの生成 (オプション):
```bash
python dummy_data.py --generate
```

4. アプリケーションの起動:
```bash
streamlit run main.py
```

## ファイル構成
- `main.py` - メインアプリケーション
- `data_handler.py` - データベース操作ロジック
- `db_init.py` - データベース初期化スクリプト
- `dummy_data.py` - テスト用ダミーデータ生成

## 使用技術
- Python 3
- SQLite3
- Streamlit (UIフレームワーク)

## トラブルシューティング

- コマンドが実行できない場合:
  ```bash
  # Pythonモジュールのパスを通す
  export PYTHONPATH=$PYTHONPATH:$(pwd)
  
  # Windowsの場合
  set PYTHONPATH=%PYTHONPATH%;%cd%
  ```

## ライセンス
MIT
