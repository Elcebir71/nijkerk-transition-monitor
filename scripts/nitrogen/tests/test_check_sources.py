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

    def test_a_text_page_instead_of_json_is_a_check_error(self):
        class NotJson(FakeResponse):
            def json(self):
                raise ValueError("Expecting value")
        with mock.patch.object(cs.requests, "get", return_value=NotJson(text="<html>Onderhoud</html>")):
            with self.assertRaises(cs.CheckError) as caught:
                cs.check_cbs_livestock()
        self.assertIn("not JSON", str(caught.exception))

    def test_one_source_with_an_unforeseen_answer_does_not_stop_the_others(self):
        def broken():
            raise KeyError("properties")
        checks = {"first": ("First", broken), "second": ("Second", lambda: {"value": 1})}
        with mock.patch.object(cs, "CHECKS", checks):
            results = cs.run_checks()
        self.assertIn("unexpected answer (KeyError", results["first"]["error"])
        self.assertEqual(results["second"], {"fingerprint": {"value": 1}})

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

    @staticmethod
    def habitat_fingerprint(everywhere, in_map_area):
        """Answer the request with a bbox from one list and the request without it from the other."""
        def answer(url, params=None, **_):
            return FakeResponse(payload={"features": in_map_area if "bbox" in params else everywhere})
        with mock.patch.object(cs.requests, "get", side_effect=answer):
            return cs.check_aerius_habitats()

    def test_habitats_counts_follow_the_map_area_request(self):
        veluwe = [habitat_feature("Veluwe", "H4030", 714, 0.9), habitat_feature("Veluwe", "ZGH5130", 1071, 1.0)]
        outside = [habitat_feature("Veluwe", "H7110A", 500, 1.0), habitat_feature("Elders", "H2130", 714, 1.0)]
        near = [habitat_feature("Rijntakken", "H6120", 1000, 1.0)]
        result = self.habitat_fingerprint(veluwe + outside + near, veluwe + near)
        self.assertEqual(result["records_netherlands"], 5)
        self.assertEqual(result["records_in_map_area"], 3)
        self.assertEqual(result["habitat_types_veluwe_in_map_area"], 2)

    def test_habitats_fingerprint_changes_when_a_type_disappears_from_the_map_area(self):
        features = [habitat_feature("Veluwe", "H4030", 714, 0.9), habitat_feature("Veluwe", "ZGH5130", 1071, 1.0),
                    habitat_feature("Rijntakken", "H6120", 1000, 1.0)]
        before = self.habitat_fingerprint(features, features)
        after = self.habitat_fingerprint(features, [features[0], features[2]])
        self.assertEqual(before["habitat_types_veluwe_in_map_area"], 2)
        self.assertEqual(after["habitat_types_veluwe_in_map_area"], 1)
        self.assertNotEqual(before["hash_in_map_area"], after["hash_in_map_area"])
        self.assertEqual(before["hash_netherlands"], after["hash_netherlands"])
        # the order in which the service returns features must not matter
        self.assertEqual(before, self.habitat_fingerprint(list(reversed(features)), list(reversed(features))))

    def test_habitats_change_elsewhere_leaves_the_map_area_hash_alone(self):
        here = [habitat_feature("Veluwe", "H4030", 714, 0.9)]
        a = self.habitat_fingerprint(here + [habitat_feature("Elders", "H2130", 714, 1.0)], here)
        b = self.habitat_fingerprint(here + [habitat_feature("Elders", "H2130", 1071, 1.0)], here)
        self.assertEqual(a["hash_in_map_area"], b["hash_in_map_area"])
        self.assertNotEqual(a["hash_netherlands"], b["hash_netherlands"])

    def test_habitats_map_area_request_uses_the_box_of_the_page(self):
        calls = []
        def answer(url, params=None, **_):
            calls.append(params)
            return FakeResponse(payload={"features": [habitat_feature("Veluwe", "H4030", 714, 0.9)]})
        with mock.patch.object(cs.requests, "get", side_effect=answer):
            cs.check_aerius_habitats()
        boxed = [params for params in calls if "bbox" in params]
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(boxed), 1)
        self.assertTrue(boxed[0]["bbox"].startswith("140411,449181,186929,490103,"))
        self.assertEqual(boxed[0]["srsName"], "urn:ogc:def:crs:EPSG::28992")
        self.assertNotIn("geometry", boxed[0]["propertyName"])

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
            delivered, message = cs.open_issue(["line"])
        self.assertFalse(delivered)
        self.assertIn("No issue opened", message)
        get.assert_not_called()
        post.assert_not_called()

    def test_opens_one_issue_with_the_label(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload=[])), \
                mock.patch.object(cs.requests, "post", return_value=FakeResponse(payload={"number": 12})) as post:
            delivered, message = cs.open_issue(["CHANGED         CBS"])
        self.assertTrue(delivered)
        self.assertEqual(message, "Opened issue #12.")
        url, kwargs = post.call_args.args[0], post.call_args.kwargs
        self.assertEqual(url, "https://api.github.com/repos/owner/repo/issues")
        self.assertEqual(kwargs["json"]["labels"], [cs.ISSUE_LABEL])
        self.assertIn("CHANGED         CBS", kwargs["json"]["body"])

    def test_an_open_issue_gets_a_comment_instead_of_a_second_issue(self):
        open_issues = [{"number": 3, "title": "Something else"},
                       {"number": 5, "title": cs.ISSUE_TITLE, "pull_request": {}},
                       {"number": 7, "title": cs.ISSUE_TITLE}]
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload=open_issues)), \
                mock.patch.object(cs.requests, "post", return_value=FakeResponse(payload={})) as post:
            delivered, message = cs.open_issue(["line"])
        self.assertTrue(delivered)
        self.assertEqual(message, "Added the report to open issue #7.")
        self.assertTrue(post.call_args.args[0].endswith("/issues/7/comments"))

    def test_other_open_issues_do_not_count_as_an_earlier_report(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(payload=[{"number": 3, "title": "Other"}])), \
                mock.patch.object(cs.requests, "post", return_value=FakeResponse(payload={"number": 4})) as post:
            delivered, message = cs.open_issue(["line"])
        self.assertEqual(message, "Opened issue #4.")
        self.assertTrue(post.call_args.args[0].endswith("/issues"))

    def test_a_failed_request_is_reported_without_the_token(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", side_effect=cs.requests.ConnectionError("down")):
            delivered, message = cs.open_issue(["line"])
        self.assertFalse(delivered)
        self.assertIn("Could not open an issue", message)
        self.assertNotIn("not-a-real-token", message)

    def test_a_refused_token_is_a_failed_delivery(self):
        with mock.patch.dict(cs.os.environ, self.ENV, clear=True), \
                mock.patch.object(cs.requests, "get", return_value=FakeResponse(status=401, payload={"message": "Bad credentials"})):
            delivered, message = cs.open_issue(["line"])
        self.assertFalse(delivered)
        self.assertNotIn("not-a-real-token", message)


class ExitCodeTests(unittest.TestCase):
    """What a scheduled job sees: 0 means nothing left to do."""

    STATE = {"written_on": "2026-10-07", "sources": {"only": {"value": 1}},
             "manual": {key: {"checked_on": date.today().isoformat()} for key in cs.MANUAL_SOURCES}}

    def run_main(self, arguments, fingerprint, issue_result=None):
        checks = {"only": ("Only source", lambda: fingerprint)}
        with mock.patch.object(cs, "CHECKS", checks), mock.patch.object(cs, "read_state", return_value=self.STATE), \
                mock.patch.object(cs.sys, "argv", ["check_sources.py"] + arguments), \
                mock.patch.object(cs, "open_issue", return_value=issue_result) as issue:
            return cs.main(), issue

    def test_nothing_changed_is_zero_and_opens_no_issue(self):
        code, issue = self.run_main(["--issue"], {"value": 1})
        self.assertEqual(code, 0)
        issue.assert_not_called()

    def test_change_without_issue_option_is_one(self):
        code, issue = self.run_main([], {"value": 2})
        self.assertEqual(code, 1)
        issue.assert_not_called()

    def test_change_put_in_an_issue_is_zero(self):
        code, issue = self.run_main(["--issue"], {"value": 2}, (True, "Opened issue #1."))
        self.assertEqual(code, 0)
        issue.assert_called_once()

    def test_change_that_could_not_be_reported_is_three(self):
        code, _ = self.run_main(["--issue"], {"value": 2}, (False, "Could not open an issue: down"))
        self.assertEqual(code, 3)

    def test_unreadable_state_is_two(self):
        with mock.patch.object(cs, "read_state", side_effect=cs.CheckError("HTTP 404")), \
                mock.patch.object(cs.sys, "argv", ["check_sources.py", "--state", "https://example.invalid/state.json"]):
            self.assertEqual(cs.main(), 2)


if __name__ == "__main__":
    unittest.main()
