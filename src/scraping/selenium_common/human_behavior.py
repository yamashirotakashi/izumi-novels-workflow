"""
人間らしい動作パターンの統一実装
bot検知回避のための自然な動作シミュレーション
"""
import asyncio
import random
import logging
from dataclasses import dataclass
from typing import Optional
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


@dataclass
class HumanBehavior:
    """人間らしい動作パラメータの統一定義"""
    # タイピング速度（秒）
    typing_speed_min: float = 0.05
    typing_speed_max: float = 0.15
    
    # マウス移動
    mouse_move_steps: int = 10
    
    # スクロール動作
    scroll_pause_min: float = 0.5
    scroll_pause_max: float = 2.0
    
    # ページ読み込み待機
    page_load_wait_min: float = 2.0
    page_load_wait_max: float = 5.0
    
    # ランダム間隔確率
    random_pause_probability: float = 0.1
    random_pause_min: float = 0.3
    random_pause_max: float = 0.8


class HumanBehaviorSimulator:
    """人間らしい動作シミュレーター"""
    
    def __init__(self, behavior: Optional[HumanBehavior] = None):
        """
        Args:
            behavior: 動作パラメータ（デフォルトを使用する場合はNone）
        """
        self.behavior = behavior or HumanBehavior()
        
    async def human_pause(self, min_seconds: float, max_seconds: float):
        """人間らしい待機"""
        pause_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(pause_time)
        
    async def human_type(self, element: WebElement, text: str):
        """人間らしいタイピング"""
        try:
            for char in text:
                element.send_keys(char)
                
                # タイピング速度をランダム化
                typing_delay = random.uniform(
                    self.behavior.typing_speed_min,
                    self.behavior.typing_speed_max
                )
                await asyncio.sleep(typing_delay)
                
                # 時々少し長い間隔（人間の癖を模倣）
                if random.random() < self.behavior.random_pause_probability:
                    await asyncio.sleep(random.uniform(
                        self.behavior.random_pause_min,
                        self.behavior.random_pause_max
                    ))
            
            logger.debug(f"人間らしいタイピング完了: '{text}'")
            
        except Exception as e:
            logger.error(f"タイピングエラー: {e}")
            raise
    
    async def human_clear_input(self, element: WebElement):
        """人間らしい入力クリア"""
        try:
            # フィールドをクリック
            element.click()
            await self.human_pause(0.2, 0.5)
            
            # 全選択してクリア
            element.send_keys(Keys.CONTROL + "a")
            await self.human_pause(0.1, 0.3)
            element.send_keys(Keys.DELETE)
            await self.human_pause(0.2, 0.4)
            
        except Exception as e:
            logger.debug(f"入力クリアエラー: {e}")
            
    async def human_submit_search(self, search_input: WebElement, driver):
        """人間らしい検索実行"""
        try:
            # 方法1: Enterキー
            search_input.send_keys(Keys.RETURN)
            logger.debug("Enterキーで検索実行")
            
        except Exception as e:
            # 方法2: 検索ボタンをクリック
            try:
                from selenium.webdriver.common.by import By
                
                button_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.search-button',
                    '.btn-search',
                    'button[class*="search"]',
                    '[value="検索"]'
                ]
                
                for selector in button_selectors:
                    try:
                        button = driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.debug(f"検索ボタンクリック: {selector}")
                            return
                    except:
                        continue
                
                logger.warning("検索実行方法が見つかりません")
                
            except Exception as e2:
                logger.error(f"検索実行エラー: {e}, {e2}")
                raise
                
    async def human_scroll(self, driver, min_pixels: int, max_pixels: int):
        """人間らしいスクロール"""
        try:
            scroll_amount = random.randint(min_pixels, max_pixels)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            await self.human_pause(
                self.behavior.scroll_pause_min,
                self.behavior.scroll_pause_max
            )
        except Exception as e:
            logger.debug(f"スクロールエラー: {e}")
            
    async def wait_for_page_load(self):
        """ページ読み込み待機（人間らしい）"""
        await self.human_pause(
            self.behavior.page_load_wait_min,
            self.behavior.page_load_wait_max
        )