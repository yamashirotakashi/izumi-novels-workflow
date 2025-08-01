#!/usr/bin/env python3
"""
設定管理システム - 段階1実装
Git履歴管理 + 自動バックアップ機能
"""
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class ConfigManager:
    """設定ファイル管理システム（段階1：Git履歴管理）"""
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent.parent / "config" / "site_selectors.json"
        self.backup_dir = self.config_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Git リポジトリ初期化
        self._ensure_git_repo()
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """ロガー設定"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _ensure_git_repo(self):
        """Git リポジトリの確認・初期化"""
        git_dir = self.config_path.parent / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(["git", "init"], cwd=self.config_path.parent, capture_output=True)
                subprocess.run(["git", "config", "user.name", "IzumiNovels-Workflow"], 
                             cwd=self.config_path.parent, capture_output=True)
                subprocess.run(["git", "config", "user.email", "system@izuminovels.local"], 
                             cwd=self.config_path.parent, capture_output=True)
                self.logger.info("Git リポジトリを初期化しました")
            except Exception as e:
                self.logger.warning(f"Git 初期化エラー: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            return self._create_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイルの解析エラー: {e}")
            return self._create_default_config()
    
    def save_config(self, config: Dict[str, Any], reason: str = "設定更新"):
        """設定ファイル保存 + Git コミット"""
        try:
            # バックアップ作成
            self._create_backup()
            
            # 設定ファイル保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Git コミット
            self._git_commit(reason)
            
            self.logger.info(f"設定ファイル保存完了: {reason}")
            
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
            # バックアップから復旧を試行
            self._restore_from_backup()
    
    def _create_backup(self):
        """設定ファイルのバックアップ作成"""
        if self.config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"site_selectors_{timestamp}.json"
            shutil.copy2(self.config_path, backup_path)
            
            # 古いバックアップファイルを削除（30個まで保持）
            backups = sorted(self.backup_dir.glob("site_selectors_*.json"))
            if len(backups) > 30:
                for old_backup in backups[:-30]:
                    old_backup.unlink()
    
    def _git_commit(self, message: str):
        """Git コミット実行"""
        try:
            config_dir = self.config_path.parent
            subprocess.run(["git", "add", self.config_path.name], 
                         cwd=config_dir, capture_output=True, check=True)
            
            commit_message = f"[AutoCommit] {message} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_message], 
                         cwd=config_dir, capture_output=True, check=True)
            
            self.logger.info(f"Git コミット完了: {message}")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Git コミット失敗: {e}")
        except Exception as e:
            self.logger.warning(f"Git コミットエラー: {e}")
    
    def get_change_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """変更履歴取得"""
        try:
            config_dir = self.config_path.parent
            result = subprocess.run(
                ["git", "log", "--oneline", f"-{limit}", self.config_path.name], 
                cwd=config_dir, capture_output=True, text=True, check=True
            )
            
            history = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        commit_hash = parts[0]
                        message = parts[1]
                        
                        # より詳細な情報を取得
                        detail_result = subprocess.run(
                            ["git", "show", "--format=%ci", "--name-only", commit_hash],
                            cwd=config_dir, capture_output=True, text=True
                        )
                        
                        if detail_result.returncode == 0:
                            lines = detail_result.stdout.strip().split('\n')
                            timestamp = lines[0] if lines else "不明"
                        else:
                            timestamp = "不明"
                        
                        history.append({
                            'commit': commit_hash,
                            'message': message,
                            'timestamp': timestamp
                        })
            
            return history
            
        except subprocess.CalledProcessError:
            self.logger.warning("Git履歴取得失敗")
            return []
        except Exception as e:
            self.logger.warning(f"履歴取得エラー: {e}")
            return []
    
    def rollback_to_commit(self, commit_hash: str) -> bool:
        """指定コミットへのロールバック"""
        try:
            config_dir = self.config_path.parent
            
            # 現在の変更を保存
            self._create_backup()
            
            # 指定コミットの内容を取得
            result = subprocess.run(
                ["git", "show", f"{commit_hash}:{self.config_path.name}"],
                cwd=config_dir, capture_output=True, text=True, check=True
            )
            
            # ファイルに書き込み
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            # 新しいコミットとして記録
            self._git_commit(f"ロールバック to {commit_hash}")
            
            self.logger.info(f"ロールバック完了: {commit_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"ロールバックエラー: {e}")
            self._restore_from_backup()
            return False
    
    def _restore_from_backup(self):
        """最新バックアップから復旧"""
        try:
            backups = sorted(self.backup_dir.glob("site_selectors_*.json"))
            if backups:
                latest_backup = backups[-1]
                shutil.copy2(latest_backup, self.config_path)
                self.logger.info(f"バックアップから復旧: {latest_backup}")
        except Exception as e:
            self.logger.error(f"バックアップ復旧エラー: {e}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """デフォルト設定作成"""
        default_config = {
            "sites": {},
            "global_settings": {
                "chrome_options": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ],
                "retry_attempts": 3,
                "timeout_default": 10
            },
            "version": "1.0.0",
            "created": datetime.now().isoformat()
        }
        
        # デフォルト設定を保存
        self.save_config(default_config, "デフォルト設定作成")
        return default_config
    
    def update_site_selector(self, site: str, selector_type: str, new_selectors: List[str], reason: str = "セレクタ更新"):
        """サイトセレクタ更新"""
        config = self.load_config()
        
        if site not in config.get("sites", {}):
            self.logger.error(f"サイトが見つかりません: {site}")
            return False
        
        # 旧セレクタをバックアップ情報として記録
        old_selectors = config["sites"][site]["selectors"].get(selector_type, [])
        
        # 新しいセレクタを設定
        config["sites"][site]["selectors"][selector_type] = new_selectors
        
        # メタデータ更新
        if "metadata" not in config["sites"][site]:
            config["sites"][site]["metadata"] = {}
        
        config["sites"][site]["metadata"]["last_updated"] = datetime.now().isoformat()
        config["sites"][site]["metadata"][f"{selector_type}_history"] = {
            "old": old_selectors,
            "new": new_selectors,
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存
        detailed_reason = f"{reason} - {site}.{selector_type}: {len(old_selectors)}→{len(new_selectors)}個"
        self.save_config(config, detailed_reason)
        
        return True
    
    def add_new_site(self, site_name: str, site_config: Dict[str, Any], reason: str = "新サイト追加"):
        """新サイト追加"""
        config = self.load_config()
        
        # サイト設定にメタデータ追加
        site_config["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "created_by": "ConfigManager"
        }
        
        config["sites"][site_name] = site_config
        
        self.save_config(config, f"{reason} - {site_name}")
        return True