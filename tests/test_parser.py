import unittest
from hypothesis import given, strategies as st
import urllib.parse
import os
import sys

# Add resources/lib to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources', 'lib'))

from parser import decode_filename, Cartoon


class TestParser(unittest.TestCase):
    
    @given(st.text(alphabet=st.characters(min_codepoint=0x0400, max_codepoint=0x04FF), min_size=1))
    def test_decode_filename_round_trip(self, original_text):
        """
        Property 2: URL Decoding Round-Trip
        Validates: Requirements 3.2
        
        For any valid Cyrillic string, encoding then decoding should preserve the content.
        """
        # Add a file extension to test removal
        filename_with_ext = original_text + ".avi"
        
        # Encode the filename
        encoded = urllib.parse.quote(filename_with_ext, encoding='utf-8')
        
        # Decode using our function
        decoded = decode_filename(encoded)
        
        # Should get back the original text without extension
        self.assertEqual(decoded, original_text)
    
    def test_decode_filename_basic_examples(self):
        """Test decode_filename with known examples."""
        # Test basic Cyrillic decoding
        encoded = "%D0%9C%D0%B0%D1%88%D0%B0.avi"  # "Маша.avi"
        expected = "Маша"
        result = decode_filename(encoded)
        self.assertEqual(result, expected)
        
        # Test with different extension
        encoded = "%D0%9D%D1%83%2C%20%D0%BF%D0%BE%D0%B3%D0%BE%D0%B4%D0%B8.mp4"  # "Ну, погоди.mp4"
        expected = "Ну, погоди"
        result = decode_filename(encoded)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()

from parser import parse_catalog
from cache import save_cache, load_cache, clear_cache

class TestParseCatalog(unittest.TestCase):
    
    @given(st.lists(
        st.tuples(
            st.text(alphabet=st.characters(min_codepoint=0x0400, max_codepoint=0x04FF), min_size=1),
            st.sampled_from(['.avi', '.mp4', '.mkv', '.flv'])
        ),
        min_size=1,
        max_size=10
    ))
    def test_parse_catalog_video_link_extraction(self, video_files):
        """
        Property 1: Video Link Extraction
        Validates: Requirements 3.1
        
        For any valid HTML page containing anchor tags with href attributes 
        pointing to video files, the parser SHALL extract all such links without missing any.
        """
        base_url = "https://example.com/multiki/"
        
        # Создать HTML с видео ссылками
        html_parts = ['<html><body>']
        expected_count = 0
        
        for filename_base, extension in video_files:
            # URL-encode filename для реалистичности
            encoded_filename = urllib.parse.quote(filename_base + extension, encoding='utf-8')
            html_parts.append(f'<a href="{encoded_filename}">Link</a>')
            expected_count += 1
        
        html_parts.append('</body></html>')
        html = '\n'.join(html_parts)
        
        # Парсить каталог
        result = parse_catalog(html, base_url)
        
        # Проверить, что извлечены все видео ссылки
        self.assertEqual(len(result), expected_count)
        
        # Проверить, что все результаты - это видео файлы
        for cartoon in result:
            self.assertIn(cartoon.extension.lower(), {'.avi', '.mp4', '.mkv', '.flv'})
            self.assertTrue(cartoon.url.startswith(base_url))
    
    def test_parse_catalog_basic_examples(self):
        """Test parse_catalog with known HTML examples."""
        base_url = "https://multiki.arjlover.net/multiki/"
        
        html = '''
        <html>
        <body>
        <a href="%D0%9C%D0%B0%D1%88%D0%B0.avi">Маша</a>
        <a href="%D0%9C%D0%B0%D1%88%D0%B0.jpg">Маша thumbnail</a>
        <a href="%D0%9D%D1%83%2C%20%D0%BF%D0%BE%D0%B3%D0%BE%D0%B4%D0%B8.mp4">Ну, погоди</a>
        <a href="some_text_file.txt">Not a video</a>
        </body>
        </html>
        '''
        
        result = parse_catalog(html, base_url)
        
        # Должно быть 2 видео файла
        self.assertEqual(len(result), 2)
        
        # Проверить первый мультфильм
        masha = next((c for c in result if c.title == "Маша"), None)
        self.assertIsNotNone(masha)
        self.assertEqual(masha.extension, ".avi")
        self.assertEqual(masha.url, base_url + "%D0%9C%D0%B0%D1%88%D0%B0.avi")
        self.assertEqual(masha.thumbnail, base_url + "%D0%9C%D0%B0%D1%88%D0%B0.jpg")
        
        # Проверить второй мультфильм
        nu_pogodi = next((c for c in result if c.title == "Ну, погоди"), None)
        self.assertIsNotNone(nu_pogodi)
        self.assertEqual(nu_pogodi.extension, ".mp4")
        self.assertEqual(nu_pogodi.thumbnail, "")  # Нет соответствующего изображения


class TestCache(unittest.TestCase):
    
    def setUp(self):
        """Очистить кэш перед каждым тестом."""
        clear_cache()
    
    def tearDown(self):
        """Очистить кэш после каждого теста."""
        clear_cache()
    
    @given(st.lists(
        st.builds(
            Cartoon,
            title=st.text(alphabet=st.characters(min_codepoint=0x0400, max_codepoint=0x04FF), min_size=1),
            url=st.text(min_size=10).map(lambda x: f"https://example.com/{x}"),
            extension=st.sampled_from(['.avi', '.mp4', '.mkv', '.flv']),
            thumbnail=st.text(min_size=0).map(lambda x: f"https://example.com/{x}.jpg" if x else "")
        ),
        min_size=0,
        max_size=10
    ))
    def test_cache_round_trip(self, cartoons):
        """
        Property 4: Cache Round-Trip
        Validates: Requirements 4.1, 4.2
        
        For any list of Cartoon objects, saving to cache and then loading from cache 
        SHALL return an equivalent list of Cartoon objects.
        """
        # Сохранить в кэш
        save_cache(cartoons)
        
        # Загрузить из кэша
        loaded_cartoons = load_cache()
        
        # Проверить, что загруженные данные эквивалентны исходным
        self.assertIsNotNone(loaded_cartoons)
        self.assertEqual(len(loaded_cartoons), len(cartoons))
        
        # Проверить каждый мультфильм
        for original, loaded in zip(cartoons, loaded_cartoons):
            self.assertEqual(original.title, loaded.title)
            self.assertEqual(original.url, loaded.url)
            self.assertEqual(original.extension, loaded.extension)
            self.assertEqual(original.thumbnail, loaded.thumbnail)