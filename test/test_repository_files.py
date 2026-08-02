import base64
import configparser
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_repository_files.py"
PUBLIC_KEY = ROOT / "keys" / "flatpak-repo-signing-public.asc"
FINGERPRINT = "34DA05F98B42968BCCCDDF1B35831D1AE820C955"
SPEC = importlib.util.spec_from_file_location("render_repository_files", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepositoryFilesTest(unittest.TestCase):
    def render(self, output: Path) -> None:
        MODULE.render_repository_files(
            output,
            "0.5.0-beta.13",
            PUBLIC_KEY,
            FINGERPRINT,
        )

    def test_renders_signed_stable_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.render(output)

            repo = configparser.ConfigParser(interpolation=None)
            repo.read(output / "dart-flutter-demo.flatpakrepo")
            ref = configparser.ConfigParser(interpolation=None)
            ref.read(output / "dart-flutter-demo.flatpakref")

            self.assertEqual(
                repo["Flatpak Repo"]["Url"],
                "https://vincentzyuapps.github.io/flatpak-repo/repo/",
            )
            self.assertEqual(repo["Flatpak Repo"]["DefaultBranch"], "stable")
            self.assertEqual(
                ref["Flatpak Ref"]["Name"],
                "io.github.vincentzyuapps.dartflutterdemo",
            )
            self.assertEqual(ref["Flatpak Ref"]["Branch"], "stable")
            self.assertGreater(
                len(base64.b64decode(ref["Flatpak Ref"]["GPGKey"])),
                1000,
            )

    def test_renders_public_metadata_without_private_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.render(output)
            metadata = json.loads((output / "repository.json").read_text())
            self.assertEqual(metadata["version"], "0.5.0-beta.13")
            self.assertEqual(metadata["fingerprint"], FINGERPRINT)
            self.assertTrue((output / "flatpak-repo-signing-public.asc").is_file())
            combined = "\n".join(
                path.read_text(encoding="utf-8")
                for path in output.iterdir()
                if path.is_file()
            )
            self.assertNotIn("PRIVATE KEY", combined)

    def test_rejects_invalid_version_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaises(ValueError):
                MODULE.render_repository_files(
                    output,
                    "../release",
                    PUBLIC_KEY,
                    FINGERPRINT,
                )
            with self.assertRaises(ValueError):
                MODULE.render_repository_files(
                    output,
                    "0.5.0",
                    PUBLIC_KEY,
                    "35831D1AE820C955",
                )


class WorkflowTest(unittest.TestCase):
    def test_publish_workflow_uses_production_environment_and_pinned_actions(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("environment: flatpak-production", workflow)
        self.assertIn("publish-v*", workflow)
        self.assertIn("repo-state", workflow)
        self.assertIn("actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", workflow)
        self.assertNotIn('echo "$PRIVATE_KEY"', workflow)
        self.assertNotIn('echo "$PASSPHRASE"', workflow)


if __name__ == "__main__":
    unittest.main()
