import unittest
from hypothesis import given, strategies as st
import urllib.parse
import os
import sys

# Add resources/lib to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources', 'lib'))

from parser import Cartoon, parse_catalog
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
        base_url = "https://example.com/multiki/"
        
        html_parts = ['<table>']
        expected_count = 0
        
        for i, (filename_base, extension) in enumerate(video_files):
            encoded_filename = urllib.parse.quote(filename_base, encoding='utf-8')
            row_class = "o" if i % 2 == 0 else "e"
            
            html_parts.append(f'''
            <tr class={row_class}>
                <td class=a>{i+1}</td>
                <td class=l><a href="http://example.com/info/{encoded_filename}{extension}.html">{filename_base}</a></td>
                <td class=r>100000000</td>
                <td>640x480</td>
                <td>00:10:00</td>
                <td><a href="http://example.com/multiki/{encoded_filename}{extension}">http</a></td>
            </tr>
            ''')
            expected_count += 1
        
        html_parts.append('</table>')
        html = '\n'.join(html_parts)
        
        result = parse_catalog(html, base_url)
        
        self.assertEqual(len(result), expected_count)
        
        for cartoon in result:
            self.assertIn(cartoon.extension.lower(), {'.avi', '.mp4', '.mkv', '.flv'})
            self.assertTrue(cartoon.url.startswith("http://example.com/multiki/"))
    
    def test_parse_catalog_basic_examples(self):
        base_url = "https://multiki.arjlover.net/multiki/"
        
        html = '''
        <table>
        <tr class=o>
            <td class=a>1</td>
            <td class=l><a href="http://multiki.arjlover.net/info/13.reis.avi.html">13 рейс</a></td>
            <td class=r>106639360</td>
            <td>640x480</td>
            <td>00:09:44</td>
            <td><a href="http://multiki.arjlover.net/multiki/13.reis.avi">http</a></td>
        </tr>
        <tr class=e>
            <td class=a>2</td>
            <td class=l><a href="http://multiki.arjlover.net/info/masha.avi.html">Маша и медведь</a></td>
            <td class=r>200000000</td>
            <td>720x576</td>
            <td>00:15:30</td>
            <td><a href="http://multiki.arjlover.net/multiki/masha.avi">http</a></td>
        </tr>
        </table>
        '''
        
        result = parse_catalog(html, base_url)
        
        self.assertEqual(len(result), 2)
        
        reis = next((c for c in result if c.title == "13 рейс"), None)
        self.assertIsNotNone(reis)
        self.assertEqual(reis.extension, ".avi")
        self.assertEqual(reis.url, "http://multiki.arjlover.net/multiki/13.reis.avi")
        self.assertEqual(reis.duration, "00:09:44")
        
        masha = next((c for c in result if c.title == "Маша и медведь"), None)
        self.assertIsNotNone(masha)
        self.assertEqual(masha.extension, ".avi")
        self.assertEqual(masha.url, "http://multiki.arjlover.net/multiki/masha.avi")


class TestCache(unittest.TestCase):
    
    def setUp(self):
        clear_cache()
    
    def tearDown(self):
        clear_cache()
    
    @given(st.lists(
        st.builds(
            Cartoon,
            title=st.text(alphabet=st.characters(min_codepoint=0x0400, max_codepoint=0x04FF), min_size=1),
            url=st.text(min_size=10).map(lambda x: f"https://example.com/{x}"),
            extension=st.sampled_from(['.avi', '.mp4', '.mkv', '.flv']),
            thumbnail=st.text(min_size=0).map(lambda x: f"https://example.com/{x}.jpg" if x else ""),
            info_url=st.just(""),
            duration=st.just(""),
            plot=st.just("")
        ),
        min_size=0,
        max_size=10
    ))
    def test_cache_round_trip(self, cartoons):
        save_cache(cartoons)
        loaded_cartoons = load_cache()
        
        self.assertIsNotNone(loaded_cartoons)
        self.assertEqual(len(loaded_cartoons), len(cartoons))
        
        for original, loaded in zip(cartoons, loaded_cartoons):
            self.assertEqual(original.title, loaded.title)
            self.assertEqual(original.url, loaded.url)
            self.assertEqual(original.extension, loaded.extension)
            self.assertEqual(original.thumbnail, loaded.thumbnail)


if __name__ == '__main__':
    unittest.main()