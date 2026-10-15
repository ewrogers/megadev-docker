import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/project.py"
spec = importlib.util.spec_from_file_location("project", SCRIPT)
project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project)


class ProjectSafety(unittest.TestCase):
    def test_init_copies_upstream_and_creates_output_folders(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            upstream = root / "upstream/new_project"
            upstream.mkdir(parents=True)
            (upstream / "makefile").write_text("upstream project")
            destination = root / "my game"
            destination.mkdir()
            project.initialize(destination, upstream.parent)
            self.assertEqual((destination / "makefile").read_text(), "upstream project")
            self.assertTrue((destination / "build").is_dir())
            self.assertTrue((destination / "disc").is_dir())
            (destination / "makefile").write_text("my changes")
            with self.assertRaisesRegex(ValueError, "empty folder"):
                project.initialize(destination, upstream.parent)
            self.assertEqual((destination / "makefile").read_text(), "my changes")

    def test_data_cue_preserves_spaces_and_never_replaces_existing_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "my game.iso"
            image.write_bytes(b"SEGADISCSYSTEM  ".ljust(2048, b"\0"))
            cue = project.write_cue(image)
            self.assertEqual(cue.read_text(), 'FILE "my game.iso" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
            cue.write_text("my mixed-mode layout")
            with self.assertRaises(FileExistsError):
                project.write_cue(image)
            self.assertEqual(cue.read_text(), "my mixed-mode layout")

    def test_rejects_invalid_iso_without_creating_cue(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "invalid.iso"
            for data in (b"garbage", b"SEGADISCSYSTEM  "):
                image.write_bytes(data)
                with self.assertRaises(ValueError):
                    project.write_cue(image)
                self.assertFalse(image.with_suffix(".cue").exists())


if __name__ == "__main__":
    unittest.main()
