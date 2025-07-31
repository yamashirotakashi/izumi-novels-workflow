#!/bin/bash

# プロジェクトセットアップスクリプト

echo "🚀 IzumiNovels-Workflow スクレイピング環境セットアップ"

# .envファイルの作成
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .envファイルを作成しました"
fi

# ログディレクトリの作成
mkdir -p logs
mkdir -p data/test_data
mkdir -p data/output

# Dockerイメージのビルド
echo "🔨 Dockerイメージをビルドしています..."
docker-compose build

# 依存関係の確認
echo "📦 依存関係を確認しています..."
docker-compose run --rm playwright pip list

echo "✨ セットアップが完了しました！"
echo ""
echo "次のコマンドで開発を開始できます:"
echo "  docker-compose up -d"
echo "  docker-compose exec playwright bash"