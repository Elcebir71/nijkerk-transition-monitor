"""Tests for check_sources.py. They use made-up answers and never touch the network.

Run from the repo root:
    python -m unittest discover -s scripts/nitrogen/tests -v
"""
from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_sources as cs  # noqa: E402


class FakeResponse:
    def __init__(self, status=200, payload=None, text="", headers=None):
        self.status_code = status
        self._payload = payload
        self.text = text if text else json.dumps(payload if payload is not None else {})
        self.headers = headers or {"Content-Type": "application/json"}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise cs.requests.HTTPError(f"HTTP {self.status_code}")


def habitat_feature(area, code, kdw, coverage):
    return {"properties": {"natura2000_area_name": area, "habitat_type_name": code,
                           "critical_deposition": kdw, "coverage": coverage}}


class FingerprintTests(unittest.TestCase):
    def test_cbs_reads_the_modified_date(self):
        answer = FakeResponse(payload={"value": [{"Modified": "2026-03-30T02:00:00", "Period": "2000 - 2025"}]})
        with mock.patch.object(cs.requests, "get", return_value=answer):
            self.assertEqual(cs.check_cbs_livestock(), {"modified": "2026-03-30T02:00:00", "period": "2000 - 2025"})

    def test_wfs_count_reads_number_matched(self):
        answer = FakeResponse(text='<wfs:FeatureCollection numberMatched="162" numberReturned="0"/>')
        with mock.patch.object(cs.requests, "get", return_value=answer):
            self.assertEqual(cs.wfs_count("https://example.invalid/wfs", "layer"), 162)

    def test_wfs_count_without_a_count_is_an_error(self):
        with mock.patch.object(cs.requests, "get", return_value=FakeResponse(text="<html>busy</html>")):
            with self.assertRaises(cs.CheckError):
                cs.wfs_count("https://example.invalid/wfs", "layer")

    def test_http_error_becomes_a_check_error(self):
        with mock.patch.object(cs.requests, "get", return_value=FakeResponse(status=503)):
            with self.assertRaises(cs.CheckError):
                cs.check_cbs_livestock()

    def test_rivm_sees_a_file_for_the_next_year(self):
        def head(url, **_):
            if f"_{cs.config.RIVM_GDN_YEAR}.zip" in url:
                return FakeResponse(headers={"Content-Length": "1000", "Last-Modified": "Mon, 10 Aug 2026 08:00:00 GMT"})
            return FakeResponse(status=404)
        with mock.patch.object(cs.requests, "head", side_effect=head):
            self.assertFalse(cs.check_rivm_gdn()["next_year_available"])
        with mock.patch.object(cs.requests, "head", return_value=FakeResponse(headers={"Content-Length": "1000"})):
            self.assertTrue(cs.check_rivm_gdn()["next_year_available"])

    def test_rivm_missing_current_file_is_an_error(self):
        with mock.patch.object(cs.requests, "head", return_value=FakeResponse(status=404)):
            with self.assertRaises(cs.CheckError):
                cs.check_rivm_gdn()

    def test_habitats_fingerprint_changes_when_a_type_disappears(self):
        features = [habitat_feature("Veluwe", "H4030", 714, 0.9), habitat_feature("Veluwe", "ZGH5130", 1071, 1.0),
                    habitat_feature("Rijntakken", "H6120", 1000, 1.0), habitat_feature("Elders", "H2130", 714, 1.0)]

        def fingerprint(feats):
            with mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload={"features": feats})):
                return cs.check_aerius_habitats()

        before, after = fingerprint(features), fingerprint([features[0]] + features[2:])
        self.assertEqual(before["habitat_types_veluwe"], 2)
        self.assertEqual(after["habitat_types_veluwe"], 1)
        self.assertEqual(before["records_areas_on_page"], 3)
        self.assertNotEqual(before["hash_areas_on_page"], after["hash_areas_on_page"])
        # the order in which the service returns features must not matter
        self.assertEqual(before, fingerprint(list(reversed(features))))

    def test_habitats_change_elsewhere_leaves_the_page_areas_hash_alone(self):
        base = [habitat_feature("Veluwe", "H4030", 714, 0.9), habitat_feature("Elders", "H2130", 714, 1.0)]
        changed = [base[0], habitat_feature("Elders", "H2130", 1071, 1.0)]

        def fingerprint(feats):
            with mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload={"features": feats})):
                return cs.check_aerius_habitats()

        a, b = fingerprint(base), fingerprint(changed)
        self.assertEqual(a["hash_areas_on_page"], b["hash_areas_on_page"])
        self.assertNotEqual(a["hash_netherlands"], b["hash_netherlands"])

    def test_catalogue_record_names_the_release(self):
        xml = ("<gmd:MD_Metadata><gmd:dateStamp><gco:Date>2026-10-06</gco:Date></gmd:dateStamp>"
               "<gmd:abstract>relevant zijn bevonden voor AERIUS 2026, uitgaande van</gmd:abstract></gmd:MD_Metadata>")
        with mock.patch.object(cs.requests, "get", return_value=FakeResponse(text=xml)):
            self.assertEqual(cs.check_aerius_catalogue_record(), {"releases_named": ["2026"], "record_date": "2026-10-06"})

    def test_catalogue_record_without_a_release_is_an_error(self):
        with mock.patch.object(cs.requests, "get", return_value=FakeResponse(text="<html>nothing here</html>")):
            with self.assertRaises(cs.CheckError):
                cs.check_aerius_catalogue_record()


class ReportTests(unittest.TestCase):
    TODAY = date(2026, 10, 7)

    def results(self, **overrides):
        base = {source_id: {"fingerprint": {"value": 1}} for source_id in cs.CHECKS}
        base.update(overrides)
        return base

    def state(self, **manual):
        dates = {"emissieregistratie": "2026-10-05", "aerius_monitor": "2026-10-06"}
        dates.update(manual)
        return {"written_on": "2026-10-07", "sources": {source_id: {"value": 1} for source_id in cs.CHECKS},
                "manual": {key: {"checked_on": value} for key, value in dates.items()}}

    def test_nothing_changed(self):
        lines, attention = cs.build_report(self.state(), self.results(), self.TODAY, 120)
        self.assertFalse(attention)
        self.assertFalse(any(line.startswith(("CHANGED", "COULD NOT READ", "NEW", "BY HAND, DUE")) for line in lines))

    def test_a_changed_source_is_reported_with_old_and_new_value(self):
        results = self.results(cbs_livestock={"fingerprint": {"value": 2}})
        lines, attention = cs.build_report(self.state(), results, self.TODAY, 120)
        self.assertTrue(attention)
        text = "\n".join(lines)
        self.assertIn("CHANGED         CBS", text)
        self.assertIn("value: 1 -> 2", text)

    def test_a_source_that_fails_is_reported_and_is_not_called_changed(self):
        results = self.results(rivm_gdn={"error": "HTTP 503"})
        lines, attention = cs.build_report(self.state(), results, self.TODAY, 120)
        self.assertTrue(attention)
        self.assertTrue(any(line.startswith("COULD NOT READ  RIVM") and "HTTP 503" in line for line in lines))
        self.assertFalse(any(line.startswith("CHANGED") for line in lines))

    def test_first_run_without_saved_state_reports_new(self):
        lines, attention = cs.build_report({"manual": self.state()["manual"]}, self.results(), self.TODAY, 120)
        self.assertTrue(attention)
        self.assertEqual(sum(line.startswith("NEW") for line in lines), len(cs.CHECKS))

    def test_check_by_hand_becomes_due(self):
        lines, attention = cs.build_report(self.state(emissieregistratie="2026-01-01"), self.results(), self.TODAY, 120)
        self.assertTrue(attention)
        self.assertTrue(any(line.startswith("BY HAND, DUE    Emissieregistratie") for line in lines))
        self.assertTrue(any(line.startswith("by hand         AERIUS Monitor") for line in lines))

    def test_check_by_hand_never_recorded_is_due(self):
        state = self.state()
        state["manual"]["aerius_monitor"] = {"checked_on": None}
        lines, attention = cs.build_report(state, self.results(), self.TODAY, 120)
        self.assertTrue(attention)
        self.assertTrue(any("never recorded" in line for line in lines))


class StateTests(unittest.TestCase):
    def test_failed_source_keeps_its_old_fingerprint(self):
        import tempfile
        old = {"sources": {"cbs_livestock": {"modified": "old"}, "rivm_gdn": {"year_on_page": 2025}},
               "manual": {"emissieregistratie": {"checked_on": "2026-10-05"}}}
        results = {"cbs_livestock": {"fingerprint": {"modified": "new"}}, "rivm_gdn": {"error": "HTTP 503"}}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "source_state.json"
            with mock.patch.object(cs, "STATE_PATH", target), mock.patch.object(cs.config, "REPO_ROOT", Path(folder)):
                cs.write_state(results, old, date(2026, 10, 7))
            written = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(written["sources"]["cbs_livestock"], {"modified": "new"})
        self.assertEqual(written["sources"]["rivm_gdn"], {"year_on_page": 2025})
        self.assertEqual(written["manual"]["emissieregistratie"], {"checked_on": "2026-10-05"})
        self.assertEqual(written["manual"]["aerius_monitor"], {"checked_on": None})
        self.assertEqual(written["written_on"], "2026-10-07")

    def test_committed_state_file_is_valid_and_names_the_manual_sources(self):
        state = json.loads((cs.config.REPO_ROOT / "data" / "nitrogen" / "source_state.json").read_text(encoding="utf-8"))
        self.assertEqual(set(state["manual"]), set(cs.MANUAL_SOURCES))


class IssueTests(unittest.TestCase):
    ENV = {"GITHUB_TOKEN": "not-a-real-token", "GITHUB_REPOSITORY": "owner/repo"}

    def test_without_a_token_no_request_is_made(self):
        with mock.patch.dict(cs.os.environ, {}, clear=True), mock.patch.object(cs.requests, "get") as get, \
                mock.patch.object(cs.requests, "post") as post:
            message = cs.open_issue(["line"])
        self.assertIn("No issue opened", message)
        get.assert_not_called()
        post.assert_not_called()

    def test_opens_one_issue_with_the_label(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload=[])), \
                mock.patch.object(cs.requests, "post", return_value=FakeResponse(payload={"number": 12})) as post:
            message = cs.open_issue(["CHANGED         CBS"])
        self.assertEqual(message, "Opened issue #12.")
        url, kwargs = post.call_args.args[0], post.call_args.kwargs
        self.assertEqual(url, "https://api.github.com/repos/owner/repo/issues")
        self.assertEqual(kwargs["json"]["labels"], [cs.ISSUE_LABEL])
        self.assertIn("CHANGED         CBS", kwargs["json"]["body"])

    def test_an_open_issue_gets_a_comment_instead_of_a_second_issue(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload=[{"number": 7}])), \
                mock.patch.object(cs.requests, "post", return_value=FakeResponse(payload={})) as post:
            message = cs.open_issue(["line"])
        self.assertEqual(message, "Added the report to open issue #7.")
        self.assertTrue(post.call_args.args[0].endswith("/issues/7/comments"))

    def test_the_token_is_never_printed(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", side_effect=cs.requests.ConnectionError("down")):
            message = cs.open_issue(["line"])
        self.assertIn("Could not open an issue", message)
        self.assertNotIn("not-a-real-token", message)


if __name__ == "__main__":
    unittest.main()
