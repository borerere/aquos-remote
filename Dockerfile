# 1. ベースイメージ（ラズパイのアーキテクチャに合う軽量版Python）
FROM python:3.11-slim

# 2. 作業ディレクトリを作成
WORKDIR /app

# 3. 依存ライブラリをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. ソースコードをコピー
COPY app.py .

# 5. 環境変数のデフォルト値（デプロイ時に上書き可能）
ENV TV_IP="192.168.10.24"
ENV TV_PORT=10002
ENV TV_ID="admin"
ENV TV_PASS="password"

# 6. ポート5000を公開
EXPOSE 5000

# 7. 実行
CMD ["python", "app.py"]