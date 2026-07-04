import unittest

from xquik_export import load_xquik_rows


class XquikExportTests(unittest.TestCase):
    def test_loads_json_array(self):
        rows = load_xquik_rows('[{"text":"Great update"}]')

        self.assertEqual(rows, [{"tweet": "Great update"}])

    def test_loads_nested_payload(self):
        rows = load_xquik_rows('{"results":[{"full_text":"Nested row"}]}')

        self.assertEqual(rows, [{"tweet": "Nested row"}])

    def test_loads_jsonl(self):
        rows = load_xquik_rows('{"tweet":"One"}\n{"body":"Two"}\n')

        self.assertEqual([row["tweet"] for row in rows], ["One", "Two"])

    def test_loads_csv_and_skips_blank_rows(self):
        rows = load_xquik_rows("tweet\nHello\n\n")

        self.assertEqual(rows, [{"tweet": "Hello"}])


if __name__ == "__main__":
    unittest.main()
