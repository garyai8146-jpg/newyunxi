"""Small repeatable tests for packing math and Yunxi XML import."""

import tempfile
import unittest
from pathlib import Path

from calculator import calculate_item_weight, can_fit_in_pack, repack_all_items
from data_manager import parse_yunxi_xml


class PackingTests(unittest.TestCase):
    def test_volume_to_weight(self):
        self.assertEqual(calculate_item_weight(1000, 500, 18, "普通板", {}, 0.75), 6.75)

    def test_material_thickness_override(self):
        db = {"A": {"default": 0.6, "map": {"18": 800}}}
        self.assertEqual(calculate_item_weight(1000, 500, 18, "A", db, 0.75), 7.2)

    def test_fits_and_starts_new_pack(self):
        self.assertTrue(can_fit_in_pack(10, 5, 15))
        self.assertFalse(can_fit_in_pack(10, 6, 15))
        items = [{"Weight":7}, {"Weight":7}, {"Weight":5}]
        packs, current = repack_all_items(items, 15)
        self.assertEqual(current, 2)
        self.assertEqual([len(packs[1]), len(packs[2])], [2, 1])

    def test_xml_parses_sample(self):
        xml = """<SmartDuctData><UserPackLimit>20</UserPackLimit>
        <LitsPack><PacknigData>
          <二维条码>ABC001</二维条码><订单编号>ORDER123</订单编号>
          <客户名>測試客戶</客户名><柜体名>A</柜体名><部件名>板件</部件名>
          <材料名>MDF</材料名><长度>1000</长度><宽度>500</宽度><厚度>18</厚度>
        </PacknigData></LitsPack></SmartDuctData>"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.xml"
            path.write_text(xml, encoding="utf-8")
            data, error = parse_yunxi_xml(path)
        self.assertIsNone(error)
        self.assertEqual(data["limit"], 20)
        self.assertEqual(data["items"][0]["Barcode"], "ABC001")


if __name__ == "__main__":
    unittest.main()
