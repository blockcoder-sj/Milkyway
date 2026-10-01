"""Free filing extraction keeps explicit statements and source-local identities."""
import unittest
from unittest.mock import patch
from cloud_app.company_filings import parse_report, parse_subsidiaries, subsidiary_document
from cloud_app import company_feed as feed
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_retention import preserve_previous

SOURCE = dict(label="SEC · 10-K", url="https://www.sec.gov/Archives/edgar/data/1/000000000126000001/report.htm", as_of="2026-02-25", level="primary")


class FilingExtractionTests(unittest.TestCase):
    def test_supply_roles_competition_and_original_anchors(self):
        raw = b'''<div>Manufacturing</div><div id="supply">We utilize foundries, such as Taiwan Semiconductor Manufacturing Company Limited and Samsung Electronics, to produce our semiconductor wafers. We purchase memory from SK Hynix and Micron Technology.</div><div>Competition</div><div>Our competitors include Advanced Micro Devices and Intel Corporation in accelerated computing.</div><div>Risk Factors</div><div>We could partner with Microsoft Corporation in the future. Apple is mentioned only as a market example.</div>'''
        result = parse_report(raw, "NVDA", SOURCE)
        pairs = {(r["symbol"], r["kind"]) for r in result["relations"]}
        self.assertEqual(pairs, {("TSM", "supplier"), ("005930.KS", "supplier"), ("000660.KS", "supplier"), ("MU", "supplier"), ("AMD", "competitor"), ("INTC", "competitor")})
        self.assertTrue(all("규칙으로 추출한 원문" in r["detail"] for r in result["relations"]))
        self.assertTrue(result["relations"][0]["source"]["url"].endswith("#supply"))
        CompanyKnowledge(symbol="NVDA", name="NVIDIA", **result)

    def test_partner_customer_and_subsidiary_are_explicit(self):
        raw = b'''<p>We partner with Microsoft Corporation to deliver products for our growing business customers.</p><p>Our largest customers include Apple Inc and Amazon.com for sales of our finished products.</p><p>OpenAI is our wholly-owned subsidiary for purposes of this synthetic parser example only.</p>'''
        result = parse_report(raw, "TEST", SOURCE)
        self.assertEqual({(r["name"], r["kind"]) for r in result["relations"]}, {("Microsoft", "partner"), ("Apple", "customer"), ("Amazon", "customer"), ("OpenAI", "subsidiary")})

    def test_negated_hypothetical_self_and_unnamed_mentions_do_not_create_edges(self):
        raw = b'''<p>We may purchase memory from Micron Technology when prices improve in the future.</p><p>We no longer partner with Microsoft Corporation after the termination of our agreement.</p><p>Our customers are two unnamed distributors that account for a material share of total revenue.</p><p>Our competitors include NVIDIA and several unnamed providers in our principal product market.</p><script>We partner with Apple Inc and Amazon.com to make products for our customers.</script>'''
        result = parse_report(raw, "NVDA", SOURCE)
        self.assertEqual(result["relations"], [])
        self.assertIn("추정하지 않습니다", result["report_analysis"]["detail"])

    def test_products_segments_and_risks_retain_source_and_bounded_text(self):
        raw = b'''<p>We offer processors and software products for accelerated computing and our enterprise customers.</p><p>We report our results through two reportable segments, computing and networking, and gaming products.</p><p>Our business depends on our supply chain and reliable raw materials sourced from third party manufacturers.</p>'''
        result = parse_report(raw, "TEST", SOURCE)
        for key in ("products", "segments", "drivers"):
            self.assertTrue(result[key])
            self.assertEqual(result[key][0]["source"]["as_of"], "2026-02-25")
        CompanyKnowledge(symbol="TEST", name="Test", **result)

    def test_one_supplier_keeps_distinct_roles_and_document_count_is_bounded(self):
        raw = b'''<p>We utilize foundries, such as Samsung Electronics, to produce our semiconductor wafers.</p><p>We purchase memory from Samsung Electronics to include in our accelerated computing products.</p>'''
        rows = parse_report(raw, "NVDA", SOURCE)["relations"]
        self.assertEqual(len(rows), 2)
        self.assertIn("제조", rows[0]["detail"])
        self.assertIn("메모리", rows[1]["detail"])
        large = "".join(f"<p>Our competitors include Intel Corporation in the distinct synthetic market number {i}.</p>" for i in range(100)).encode()
        self.assertEqual(len(parse_report(large, "NVDA", SOURCE)["relations"]), 80)

    def test_sec_contact_is_never_sent_to_wikipedia(self):
        import os
        with patch.dict(os.environ, {"SEC_CONTACT_EMAIL": "a@example.test"}), patch.object(feed, "respect_source_limit"), patch.object(feed, "FixedSession") as sessions, patch.object(feed, "read_requests_json", return_value={}):
            response = sessions.return_value.__enter__.return_value.get.return_value
            response.status_code = 200
            feed.get(feed.WIKI)
            self.assertEqual(sessions.return_value.__enter__.return_value.get.call_args.kwargs["headers"]["User-Agent"], feed.AGENT)

    def test_exhibit_company_names_remain_unmerged_source_local_entities(self):
        raw = b'''<h1>Exhibit 21 Subsidiaries</h1><table><tr><td>Name of Subsidiary</td><td>Jurisdiction</td></tr><tr><td>Alpha Services LLC</td><td>Delaware</td></tr><tr><td>Alpha Services LLC</td><td>Delaware</td></tr><tr><td>Beta Limited</td><td>United Kingdom</td></tr></table>'''
        rows = parse_subsidiaries(raw, SOURCE)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["symbol"] is None and r["kind"] == "subsidiary" for r in rows))
        self.assertIn("Delaware", rows[0]["detail"])
        with self.assertRaises(ValueError):
            parse_subsidiaries(b"<table><tr><td>Not an exhibit</td></tr></table>", SOURCE)

    def test_page_headers_preserve_named_competition_lists(self):
        raw = b'''<div>Competition</div><div>8</div><div>Table of Contents</div><div>Our current competitors include:</div><div>Cloud computing platforms with internal AI teams, such as Amazon and Microsoft Corporation.</div><div>Patents and Proprietary Rights</div><div>Alphabet and Intel Corporation are mentioned in a different section only as contextual examples.</div>'''
        result = parse_report(raw, "NVDA", SOURCE)
        self.assertEqual({r["symbol"] for r in result["relations"]}, {"AMZN", "MSFT"})

    def test_subsidiary_link_cannot_leave_sec_or_switch_issuer(self):
        for href in ("https://evil.test/report.htm", "https://www.sec.gov/Archives/edgar/data/2/000000000126000001/ex21.htm", "https://www.sec.gov/private.htm"):
            raw = f'<a href="{href}">Subsidiaries of Registrant</a>'.encode()
            self.assertIsNone(subsidiary_document(raw, SOURCE["url"]))
        self.assertTrue(subsidiary_document(b'<a href="subsidiaries.htm">Subsidiaries of Registrant</a>', SOURCE["url"]).endswith('/subsidiaries.htm'))

    def test_exact_official_sec_index_is_independent_of_wikidata(self):
        with patch.object(feed, "_sec_index", None), patch.object(feed, "get", return_value={"0": {"ticker": "ABCD", "cik_str": 12345}, "1": {"ticker": "BAD", "cik_str": "../etc"}}) as get:
            self.assertEqual(feed.sec_identity("ABCD"), "12345")
            self.assertIsNone(feed.sec_identity("ABC"))
            self.assertIsNone(feed.sec_identity("BAD"))
            self.assertEqual(get.call_count, 1)

    def test_sec_contact_validation_and_archive_path_validation_precede_network(self):
        import os
        with patch.object(feed, "FixedSession") as network:
            with patch.dict(os.environ, {"SEC_CONTACT_EMAIL": "a@example.test\r\nX: secret"}):
                with self.assertRaises(ValueError):
                    feed.get(SOURCE["url"])
            with patch.dict(os.environ, {"SEC_CONTACT_EMAIL": "a@example.test"}):
                for url in ("https://www.sec.gov/../../private", "https://www.sec.gov/Archives/edgar/data/1/../../file.htm", "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/.."):
                    with self.assertRaises(ValueError):
                        feed.get(url)
            network.assert_not_called()

    def test_rate_limit_pauses_only_the_host_without_retrying(self):
        from types import SimpleNamespace
        response = SimpleNamespace(status_code=429, headers={"Retry-After": "600"})
        with patch.object(feed, "_cooldowns", {}), patch.object(feed.time, "monotonic", return_value=100), patch.object(feed.time, "sleep") as sleep:
            feed.remember_source_limit("www.wikidata.org", response)
            self.assertEqual(feed._cooldowns["www.wikidata.org"], 700)
            with patch.object(feed, "FixedSession") as network:
                with self.assertRaises(feed.SourceCoolingDown):
                    feed.get(feed.WIKI)
                network.assert_not_called()
            feed.respect_source_limit("data.sec.gov")
            sleep.assert_called_once()

    def test_retry_header_is_bounded_and_diagnostics_are_redacted(self):
        from types import SimpleNamespace
        for value in ("invalid secret", "-100", "9" * 100):
            with patch.object(feed, "_cooldowns", {}), patch.object(feed.time, "monotonic", return_value=100):
                feed.remember_source_limit("www.wikidata.org", SimpleNamespace(status_code=429, headers={"Retry-After": value}))
                self.assertGreaterEqual(feed._cooldowns["www.wikidata.org"], 160)
                self.assertLessEqual(feed._cooldowns["www.wikidata.org"], 86500)
        self.assertNotIn("secret", feed.collection_error("Wikidata", RuntimeError("secret")))
        self.assertIn("대기 중", feed.collection_error("Wikidata", feed.SourceCoolingDown()))

    def test_failed_wiki_preserves_wiki_evidence_but_retracts_refreshed_sec_claims(self):
        def edge(name, origin):
            return dict(name=name, kind="subsidiary", source=origin)
        wiki = dict(label="Wikidata", url="https://www.wikidata.org/wiki/Q1", level="encyclopedia")
        old = CompanyKnowledge(symbol="TEST", name="Test", relations=[edge("Wiki child", wiki), edge("Old SEC child", SOURCE)])
        current = CompanyKnowledge(symbol="TEST", name="Test", errors=["wiki failed"], unavailable_sources=["wikidata"])
        preserve_previous(current, old)
        self.assertEqual([r.name for r in current.relations], ["Wiki child"])
        self.assertTrue(any("이전 수집" in message for message in current.errors))

    def test_sec_failure_preserves_prior_sec_edges_alongside_current_wiki_edges(self):
        wiki = dict(label="Wikidata", url="https://www.wikidata.org/wiki/Q1", level="encyclopedia")
        old = CompanyKnowledge(symbol="TEST", name="Test", relations=[dict(name="SEC supplier", kind="supplier", source=SOURCE)])
        current = CompanyKnowledge(symbol="TEST", name="Test", errors=["SEC failed"], unavailable_sources=["sec_report"], relations=[dict(name="Wiki child", kind="subsidiary", source=wiki)])
        preserve_previous(current, old)
        self.assertEqual([r.name for r in current.relations], ["Wiki child", "SEC supplier"])
        preserve_previous(current, old)
        self.assertEqual(len(current.relations), 2)

    def test_no_failure_does_not_resurrect_old_relations(self):
        old = CompanyKnowledge(symbol="TEST", name="Test", relations=[dict(name="Old", kind="supplier", source=SOURCE)])
        current = CompanyKnowledge(symbol="TEST", name="Test")
        preserve_previous(current, old)
        self.assertEqual(current.relations, [])


if __name__ == "__main__":
    unittest.main()
