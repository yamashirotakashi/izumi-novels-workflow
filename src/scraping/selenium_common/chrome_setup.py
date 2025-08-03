"""
Chrome設定の統一実装
bot検知回避設定の標準化
"""
import logging
from typing import Dict, Any, Optional
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)


class ChromeSetupManager:
    """Chrome設定管理クラス"""
    
    # デフォルトUser-Agent
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    
    # デフォルトウィンドウサイズ
    DEFAULT_WINDOW_SIZE = "1280,720"
    
    @classmethod
    def get_bot_evasion_arguments(cls) -> list:
        """bot検知回避用のChrome引数"""
        return [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            f'--window-size={cls.DEFAULT_WINDOW_SIZE}',
            f'--user-agent={cls.DEFAULT_USER_AGENT}'
        ]
    
    @classmethod
    def get_experimental_options(cls) -> Dict[str, Any]:
        """実験的オプション"""
        return {
            "excludeSwitches": ["enable-automation"],
            "useAutomationExtension": False
        }
    
    @classmethod
    def get_preferences(cls, disable_images: bool = True) -> Dict[str, Any]:
        """Chrome設定（プリファレンス）"""
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2  # 通知を無効化
            }
        }
        
        if disable_images:
            prefs["profile.managed_default_content_settings"] = {
                "images": 2  # 画像読み込み無効化（高速化）
            }
            
        return prefs
    
    @classmethod
    def setup_webdriver_stealth(cls, driver):
        """WebDriver痕跡除去のJavaScript実行"""
        try:
            # webdriver属性の除去
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # その他の自動化検出回避
            driver.execute_script("""
                delete window.chrome.runtime.onConnect;
                delete window.chrome.runtime.onMessage;
            """)
            
            logger.debug("WebDriver痕跡除去完了")
            
        except Exception as e:
            logger.debug(f"WebDriver痕跡除去エラー（影響なし）: {e}")


def get_undetected_chrome_options(
    headless: bool = True,
    disable_images: bool = True,
    custom_user_agent: Optional[str] = None,
    custom_window_size: Optional[str] = None
) -> uc.ChromeOptions:
    """
    undetected-chromedriver用の標準オプション取得
    
    Args:
        headless: ヘッドレスモード
        disable_images: 画像無効化（高速化）
        custom_user_agent: カスタムUser-Agent
        custom_window_size: カスタムウィンドウサイズ
        
    Returns:
        設定済みのChromeOptions
    """
    options = uc.ChromeOptions()
    
    # ヘッドレスモード
    if headless:
        options.add_argument('--headless=new')
    
    # bot検知回避引数
    for arg in ChromeSetupManager.get_bot_evasion_arguments():
        # カスタム設定で上書き
        if custom_user_agent and arg.startswith('--user-agent='):
            options.add_argument(f'--user-agent={custom_user_agent}')
        elif custom_window_size and arg.startswith('--window-size='):
            options.add_argument(f'--window-size={custom_window_size}')
        else:
            options.add_argument(arg)
    
    # 実験的オプション
    for key, value in ChromeSetupManager.get_experimental_options().items():
        options.add_experimental_option(key, value)
    
    # プリファレンス
    prefs = ChromeSetupManager.get_preferences(disable_images)
    options.add_experimental_option("prefs", prefs)
    
    return options


def create_undetected_chrome(
    options: Optional[uc.ChromeOptions] = None,
    headless: bool = True,
    disable_images: bool = True,
    version_main: Optional[int] = None
):
    """
    undetected-chromedriver インスタンス作成
    
    Args:
        options: カスタムオプション（Noneの場合は標準設定）
        headless: ヘッドレスモード
        disable_images: 画像無効化
        version_main: Chromeバージョン指定
        
    Returns:
        設定済みのChromeDriverインスタンス
    """
    if options is None:
        options = get_undetected_chrome_options(
            headless=headless,
            disable_images=disable_images
        )
    
    try:
        driver = uc.Chrome(options=options, version_main=version_main)
        
        # WebDriver痕跡除去
        ChromeSetupManager.setup_webdriver_stealth(driver)
        
        logger.info("undetected-chromedriver起動完了（bot検知回避設定済み）")
        return driver
        
    except Exception as e:
        logger.error(f"Chromedriver起動エラー: {e}")
        raise