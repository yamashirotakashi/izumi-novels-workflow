"""
Test suite for Phase 1.6A - Title Processing Consolidation

Verifies that the unified title processing utility maintains
all existing functionality while eliminating code duplication.
"""
import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraping.utils.title_processing import TitleProcessor, JapaneseTitleProcessor
from scraping.base_scraper import BaseScraper
from scraping.selenium_base_scraper import SeleniumBaseScraper


class TestTitleProcessingConsolidation(unittest.TestCase):
    """Test title processing consolidation functionality."""
    
    def setUp(self):
        """Set up test cases."""
        self.test_titles = [
            "課長が目覚めたら異世界SF艦隊の提督になってた件です④",
            "【重要】Python デザインパターン入門",
            "《プログラミング》　設計手法（第1巻）",
            "ファンタジー小説vol.2",
            "転生したら魔法使いになった件 volume 3"
        ]
    
    def test_unified_title_processor_normalize(self):
        """Test TitleProcessor.normalize_title functionality."""
        title = "【重要】課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        expected = "重要課長が目覚めたら異世界sf艦隊の提督になってた件です4"  # ④ is converted to 4 by NFKC
        
        result = TitleProcessor.normalize_title(title)
        self.assertEqual(result, expected)
    
    def test_base_scraper_uses_unified_processor(self):
        """Test that BaseScraper uses unified TitleProcessor."""
        title = "【重要】課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        expected = "重要課長が目覚めたら異世界sf艦隊の提督になってた件です4"  # ④ is converted to 4 by NFKC
        
        result = BaseScraper.normalize_title(title)
        self.assertEqual(result, expected)
    
    def test_selenium_base_scraper_uses_unified_processor(self):
        """Test that SeleniumBaseScraper uses unified TitleProcessor."""
        title = "【重要】課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        expected = "重要課長が目覚めたら異世界sf艦隊の提督になってた件です4"  # ④ is converted to 4 by NFKC
        
        result = SeleniumBaseScraper.normalize_title(title)
        self.assertEqual(result, expected)
    
    def test_title_matching_functionality(self):
        """Test title matching functionality."""
        expected = "課長が目覚めたら異世界SF艦隊の提督になってた件です"
        actual = "【重要】課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        
        # Test via TitleProcessor
        result1 = TitleProcessor.is_title_match(expected, actual, threshold=0.8)
        self.assertTrue(result1)
        
        # Test via static method call (BaseScraper is abstract)
        result2 = BaseScraper.normalize_title(expected) in BaseScraper.normalize_title(actual)
        self.assertTrue(result2)
    
    def test_volume_extraction(self):
        """Test volume number extraction."""
        test_cases = [
            ("課長が目覚めたら異世界SF艦隊の提督になってた件です④", 4),
            ("Python デザインパターン入門 第3巻", 3),
            ("プログラミング設計手法(2)", 2),
            ("ファンタジー小説vol.5", 5),
            ("転生魔法使い volume 7", 7),
            ("単発小説", None)
        ]
        
        for title, expected_volume in test_cases:
            with self.subTest(title=title):
                result = TitleProcessor.extract_volume_number(title)
                self.assertEqual(result, expected_volume)
    
    def test_volume_variants_generation(self):
        """Test volume variant generation."""
        title = "課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        variants = TitleProcessor.create_volume_variants(title)
        
        # Should contain different volume format variants
        self.assertIn("課長が目覚めたら異世界SF艦隊の提督になってた件です④", variants)
        self.assertIn("課長が目覚めたら異世界SF艦隊の提督になってた件です 4", variants)
        self.assertIn("課長が目覚めたら異世界SF艦隊の提督になってた件です 第4巻", variants)
        self.assertIn("課長が目覚めたら異世界SF艦隊の提督になってた件です(4)", variants)
    
    def test_japanese_specific_processing(self):
        """Test Japanese-specific title processing."""
        title = "プログラミング０１２ＡＢＣ"
        result = JapaneseTitleProcessor.normalize_japanese_title(title)
        expected = "プログラミング012abc"
        
        self.assertEqual(result, expected)
    
    def test_genre_keyword_extraction(self):
        """Test genre keyword extraction."""
        title = "課長が目覚めたら異世界SF艦隊の提督になってた件です"
        keywords = JapaneseTitleProcessor.extract_genre_keywords(title)
        
        self.assertIn("異世界", keywords)
        self.assertIn("課長", keywords)
        self.assertIn("艦隊", keywords)
        self.assertIn("提督", keywords)
    
    def test_backward_compatibility_functions(self):
        """Test backward compatibility convenience functions."""
        from scraping.utils.title_processing import (
            normalize_title, is_title_match, create_volume_variants,
            extract_volume_number, normalize_volume_notation
        )
        
        title = "【重要】課長が目覚めたら異世界SF艦隊の提督になってた件です④"
        
        # Test convenience functions work
        self.assertTrue(normalize_title(title))
        self.assertTrue(is_title_match(title, title))
        self.assertTrue(create_volume_variants(title))
        self.assertEqual(extract_volume_number(title), 4)
        self.assertTrue(normalize_volume_notation(title, 'arabic'))


class TestCodeDuplicationElimination(unittest.TestCase):
    """Test that code duplication has been successfully eliminated."""
    
    def test_base_classes_use_unified_processor(self):
        """Verify base classes delegate to unified processor."""
        # This test ensures that both base classes now use the same implementation
        title = "テスト小説④【重要】"
        
        result1 = BaseScraper.normalize_title(title)
        result2 = SeleniumBaseScraper.normalize_title(title)
        result3 = TitleProcessor.normalize_title(title)
        
        # All should produce identical results
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
        self.assertEqual(result1, result3)
    
    def test_consistent_behavior_across_frameworks(self):
        """Test consistent behavior across different framework base classes."""
        test_titles = [
            "【異世界】転生魔法使いの冒険①",
            "プログラミング設計パターン（第2巻）",
            "SF艦隊提督物語 vol.3"
        ]
        
        for title in test_titles:
            with self.subTest(title=title):
                playwright_result = BaseScraper.normalize_title(title)
                selenium_result = SeleniumBaseScraper.normalize_title(title)
                unified_result = TitleProcessor.normalize_title(title)
                
                # All implementations should produce identical results
                self.assertEqual(playwright_result, selenium_result)
                self.assertEqual(selenium_result, unified_result)


if __name__ == '__main__':
    unittest.main()