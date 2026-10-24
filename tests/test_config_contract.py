import tomllib
import unittest

from agent_foundry.config import DEFAULT_CONFIG, CoreConfig, PlannerConfig


class ConfigContractTests(unittest.TestCase):
    def test_default_config_matches_dataclasses(self):
        data = tomllib.loads(DEFAULT_CONFIG)
        self.assertEqual(set(data["core"]), set(CoreConfig.__dataclass_fields__))
        self.assertEqual(set(data["planner"]), set(PlannerConfig.__dataclass_fields__))

    def test_default_values_match(self):
        data = tomllib.loads(DEFAULT_CONFIG)
        core = CoreConfig()
        for key, value in data["core"].items():
            self.assertEqual(value, getattr(core, key), key)
