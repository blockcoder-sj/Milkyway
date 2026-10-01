"""Failure recovery and execution invariants, without an AI API call."""
import unittest
from pydantic import ValidationError
from cloud_app.research_validation import interrupted_narrative, narrative_only
from cloud_app.research_ai import ResearchReply, strict_reply_schema
from cloud_app.strategies import StrategySpec


class ResearchValidationTests(unittest.TestCase):
    def test_recovery_never_keeps_a_strategy(self):
        result = narrative_only({'reply':'  가설을 더 구체화해 보겠습니다  ',
                                 'strategy':{'arbitrary':'not executable'}})
        self.assertEqual(result['reply'], '가설을 더 구체화해 보겠습니다')
        self.assertIsNone(result['strategy'])
        for value in [None, [], {'reply':'   '}, {'reply':12},
                      {'reply':'x'*7001}, {'reply':'ok','limitations':['x'*1001]}]:
            self.assertIsNone(narrative_only(value))

    def test_only_complete_first_string_can_survive_token_interruption(self):
        result = interrupted_narrative('{"reply":"대상 종목을 확인하세요\\n규칙은 저장하지 않았습니다","strategy":{"factors":[')
        self.assertIn('\n', result['reply'])
        self.assertIsNone(result['strategy'])
        for value in ['{"reply":"끝나지 않은 문장', '{"other":{"reply":"nested"}}',
                      '{"reply":{"reply":"object"}}', '{"reply":"   "}',
                      '[{"reply":"list"}]', 'x' * (256*1024+1)]:
            self.assertIsNone(interrupted_narrative(value))

    def test_blank_prose_names_and_cancelled_signals_are_rejected(self):
        with self.assertRaises(ValidationError):
            ResearchReply(reply='   ')
        for name in ['   ', ' a ']:
            with self.assertRaises(ValidationError):
                StrategySpec(name=name, factors=[{'kind':'momentum'}])
        with self.assertRaises(ValidationError):
            StrategySpec(name='cancelled', factors=[{'kind':'momentum','weight':1},
                                                   {'kind':'momentum','weight':-1}])
        valid = StrategySpec(name=' valid ', factors=[{'kind':'momentum','lookback':20,'weight':1},
                                                     {'kind':'momentum','lookback':60,'weight':-1}])
        self.assertEqual(valid.name, 'valid')

    def test_generation_schema_reserves_output_headroom_and_keeps_legacy_reading(self):
        schema = strict_reply_schema()
        self.assertEqual(schema['properties']['reply']['maxLength'], 1600)
        self.assertEqual(schema['$defs']['StrategySpec']['properties']['description']['maxLength'], 500)
        self.assertEqual(len(ResearchReply(reply='x'*2000).reply), 2000)


if __name__ == '__main__':
    unittest.main()
