import subprocess
import unittest
from pathlib import Path


class TestE2EScript(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).parent.parent
        self.script_path = self.root_dir / "tests" / "e2e" / "run_tests.sh"

    def test_script_exists(self):
        self.assertTrue(self.script_path.exists(), "run_tests.sh should exist")

    def test_script_bash_syntax(self):
        res = subprocess.run(
            ["bash", "-n", str(self.script_path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"run_tests.sh syntax check failed: {res.stderr}",
        )

    def test_script_contains_required_redis_commands(self):
        content = self.script_path.read_text()
        self.assertIn("PING", content)
        self.assertIn("ECHO", content)
        self.assertIn("QUIT", content)


class TestEnvironmentAndHarness(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).parent.parent

    def test_required_files_exist(self):
        required = [
            "Dockerfile.e2e",
            "docker-compose.e2e.yml",
            "Makefile",
            "pyproject.toml",
            "requirements.txt",
        ]
        for fname in required:
            fpath = self.root_dir / fname
            self.assertTrue(fpath.exists(), f"Required file {fname} missing")

    def test_makefile_targets(self):
        makefile = self.root_dir / "Makefile"
        content = makefile.read_text()
        self.assertIn("test:", content)
        self.assertIn("e2e:", content)

    def test_docker_compose_services(self):
        compose_file = self.root_dir / "docker-compose.e2e.yml"
        content = compose_file.read_text()
        self.assertIn("pyedis-server", content)
        self.assertIn("test-runner-e2e", content)


if __name__ == "__main__":
    unittest.main()
