from unittest import TestCase
from ruamel.yaml import YAML
import json
from click.testing import CliRunner


from htruc.cli import cli
from htruc.utils import parse_yaml


def _sort_metrics(metrics):
    return sorted(metrics, key=lambda x: x["metric"])


class TestCLI(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def invoke(self, *args, **kwargs):
        return self.runner.invoke(cli, *args, **kwargs)

    def test_update_volume(self):
        """[CLI] Tests that update volume does the right thing"""
        rs = self.invoke(
            ["update-volumes", "tests/test_data/cremma-medieval.yml", "tests/test_data/updated_metrics.json"]
        )
        print(rs)
        new_catalog = parse_yaml("tests/test_data/cremma-medieval.auto-update.yml")
        self.assertEqual(
            _sort_metrics(new_catalog["volume"]),
            _sort_metrics([{'metric': 'characters', 'count': 481735}, {'metric': 'files', 'count': 20},
             {'metric': 'lines', 'count': 19000}, {'metric': 'regions', 'count': 1785}])
        )
        self.assertEqual(rs.exit_code, 0)
        self.assertIn("The category `lines` increased by 615", rs.output)
        self.assertIn("The category `regions` decreased by 10", rs.output)

        with self.runner.isolated_filesystem():
            with open("catalog.yml", "w") as f:
                yaml = YAML()
                yaml.default_flow_style = False
                yaml.dump(new_catalog, f)
            with open("update-metrics.json", "w") as f:
                # Add 10 files
                json.dump({"volume": [{'metric': 'files', 'count': 30}]}, f)

            rs = self.invoke(
                ["update-volumes", "catalog.yml", "update-metrics.json",
                 "--inplace"]
            )
            self.assertEqual(rs.exit_code, 0)
            self.assertIn("The category `files` increased by 10", rs.output)

            new_catalog = parse_yaml("catalog.yml")
            self.assertEqual(
                _sort_metrics(new_catalog["volume"]),
                _sort_metrics([{'metric': 'characters', 'count': 481735}, {'metric': 'files', 'count': 30},
                 {'metric': 'lines', 'count': 19000}, {'metric': 'regions', 'count': 1785}])
            )
