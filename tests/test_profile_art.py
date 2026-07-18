import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "make_ascii_svg", ROOT / "scripts" / "make_ascii_svg.py"
)
assert SPEC and SPEC.loader
ASCII = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASCII)


class AsciiPortraitAnimationTest(unittest.TestCase):
    def test_each_row_is_drawn_by_a_visible_cursor_for_over_six_seconds(self):
        rows = ["@" * ASCII.COLS for _ in range(ASCII.ROWS)]

        svg = ASCII.render(rows)

        self.assertEqual(svg.count('class="draw-cursor"'), ASCII.ROWS)
        self.assertIn('id="draw-cursor-0"', svg)
        self.assertGreaterEqual(ASCII.DRAW_TOTAL_SECONDS, 6.0)


if __name__ == "__main__":
    unittest.main()
