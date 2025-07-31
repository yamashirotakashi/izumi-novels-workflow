# Playwright Python環境
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

WORKDIR /app

# 日本語フォントのインストール（スクレイピング時の文字化け対策）
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightブラウザのインストール
RUN playwright install chromium

# アプリケーションコード
COPY . .

# 環境変数
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

CMD ["python", "-m", "pytest", "tests/", "-v"]