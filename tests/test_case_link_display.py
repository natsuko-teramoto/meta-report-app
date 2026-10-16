import unittest
import pandas as pd

from services.ad_search import build_ad_search_data, search_ads, build_customer_results


def sample():
    return {
        "customers": pd.DataFrame([
            {"Meta顧客ID": "M1", "案件名": "旧法人", "業種": "歯科"},
            {"Meta顧客ID": "M2", "案件名": "正法人", "業種": "歯科"},
        ]),
        "facilities": pd.DataFrame([
            {"施設ID": "F1", "Meta顧客ID": "M1", "施設名": "旧施設"},
            {"施設ID": "F2", "Meta顧客ID": "M2", "施設名": "正施設"},
        ]),
        "cases": pd.DataFrame([
            {"案件ID": "A1", "Meta顧客ID": "M2", "施設ID": "F2"},
        ]),
        "meta_history": pd.DataFrame([
            {"案件ID": "A1", "Meta顧客ID": "M1", "施設ID": "F1",
             "施設名": "旧施設", "ad_id": "AD1", "キャンペーン名": "広告1"},
        ]),
        "legacy_ads": pd.DataFrame(),
    }


class CorrectedLinkTests(unittest.TestCase):
    def test_api_customer_facility_and_search(self):
        data = build_ad_search_data(sample())
        self.assertEqual(data.iloc[0]["Meta顧客ID"], "M2")
        self.assertEqual(data.iloc[0]["施設ID"], "F2")
        self.assertEqual(data.iloc[0]["施設名"], "正施設")
        self.assertEqual(data.iloc[0]["ad_id"], "AD1")
        self.assertEqual(len(build_customer_results(data)), 1)
        self.assertEqual(len(search_ads(data, customer="正法人")), 1)

    def test_history_input_unchanged(self):
        master = sample()
        build_ad_search_data(master)
        self.assertEqual(master["meta_history"].iloc[0]["Meta顧客ID"], "M1")

    def test_wrong_facility_owner_rejected(self):
        master = sample()
        master["cases"].loc[0, "Meta顧客ID"] = "M1"
        with self.assertRaises(ValueError):
            build_ad_search_data(master)

    def test_missing_facility_rejected(self):
        master = sample()
        master["cases"].loc[0, "施設ID"] = "F404"
        with self.assertRaises(ValueError):
            build_ad_search_data(master)


if __name__ == "__main__":
    unittest.main()
