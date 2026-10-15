import copy
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/compare-reports.py"
spec = importlib.util.spec_from_file_location("reports", SCRIPT)
reports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reports)


def example_report(platform):
    outputs = {"payloads": {"module.mmd": {"bytes": 8, "sha256": "a" * 64}},
               "disc": {"boot": {"sha256": "b" * 64}, "files": {"FILE": {"sha256": "c" * 64}}}}
    return {"passed": True, "platform": platform, "sources": {"gcc": "locked"},
            "m68k_regression": {"compiler_default": "passed", "negative_control": "reproduced",
                                "far_branch": "passed", "cpu_policy": "passed", "libgcc_arithmetic": "passed"},
            "examples": {name: copy.deepcopy(outputs) for name in reports.CASES}}


class PublicationGate(unittest.TestCase):
    def test_matching_payloads_pass_despite_different_host_metadata(self):
        left, right = example_report("linux/arm64"), example_report("linux/amd64")
        left["image_id"], right["image_id"] = "native-arm", "native-amd"
        reports.compare(left, right)

    def test_rejects_failed_missing_or_different_results(self):
        left = example_report("linux/arm64")
        mutations = [lambda r: r.update(passed=False),
                     lambda r: r.update(platform="linux/arm64"),
                     lambda r: r["examples"].pop("gfx"),
                     lambda r: r["examples"]["new_project"].update(payloads={}),
                     lambda r: r["examples"]["gfx"]["disc"].update(files={}),
                     lambda r: r["examples"]["gfx"]["payloads"]["module.mmd"].update(sha256="d" * 64),
                     lambda r: r["m68k_regression"].pop("negative_control"),
                     lambda r: r.update(sources={"gcc": "different"})]
        for mutate in mutations:
            right = example_report("linux/amd64")
            mutate(right)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                reports.compare(left, right)


if __name__ == "__main__":
    unittest.main()
