"""Behavioral checks for independently installable Skill directories."""
from pathlib import Path
import tempfile
import unittest

from scripts.check_catalog import validate_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def skill(self, directory="example", *, name="example", body=""):
        path = self.root / "skills" / directory
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Example\n---\n\n{body}\n", encoding="utf-8"
        )
        return path

    def test_complete_independent_skill_with_nested_resources(self):
        skill = self.skill(body="[Guide](reference/guide.md#usage) [Runner](scripts/run.py)")
        (skill / "reference").mkdir()
        (skill / "scripts").mkdir()
        (skill / "reference/guide.md").write_text("[Back](../SKILL.md)\n")
        (skill / "scripts/run.py").write_text("print('hello')\n")
        self.assertEqual(validate_catalog(self.root), [])

    def test_missing_local_reference_is_reported(self):
        self.skill(body="[Guide](reference/missing.md)")
        self.assertTrue(validate_catalog(self.root))

    def test_nested_reference_file_is_checked(self):
        skill = self.skill(body="[Guide](guide.md)")
        (skill / "guide.md").write_text("[Runner](scripts/missing.py)\n")
        self.assertTrue(validate_catalog(self.root))

    def test_reference_style_missing_resource_is_reported(self):
        self.skill(body="Read [the guide][guide].\n\n[guide]: reference/missing.md")
        self.assertTrue(validate_catalog(self.root))

    def test_existing_cross_skill_link_cannot_supply_resources(self):
        self.skill("one", name="one", body="[Other](../two/SKILL.md)")
        self.skill("two", name="two")
        self.assertTrue(validate_catalog(self.root))

    def test_encoded_parent_path_cannot_escape_skill(self):
        (self.root / "secret.md").write_text("outside\n")
        self.skill(body="[Outside](%2e%2e/%2e%2e/secret.md)")
        self.assertTrue(validate_catalog(self.root))

    def test_symlink_cannot_supply_external_resources(self):
        skill = self.skill()
        external = self.root / "external.py"
        external.write_text("print('external')\n")
        (skill / "run.py").symlink_to(external)
        self.assertTrue(validate_catalog(self.root))

    def test_duplicate_declared_names_are_reported(self):
        self.skill("first", name="duplicate")
        self.skill("second", name="'duplicate'")
        self.assertTrue(validate_catalog(self.root))

    def test_shell_checkout_prerequisite_is_reported(self):
        for command in (
            "git clone https://github.com/ob-labs/ai-vision-ob.git",
            "gh repo clone ob-labs/ai-vision-ob",
            'cd "$AIV_REPO/aivision-cli"',
            "cd /work/ai-vision-ob/aivision-cli",
        ):
            with self.subTest(command=command):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    skill = root / "skills/example"
                    skill.mkdir(parents=True)
                    (skill / "SKILL.md").write_text(
                        f"---\nname: example\ndescription: Example\n---\n```sh\n{command}\n```\n"
                    )
                    self.assertTrue(validate_catalog(root))

    def test_inline_checkout_command_is_reported(self):
        self.skill(body="First run `gh repo clone ob-labs/ai-vision-ob`.")
        self.assertTrue(validate_catalog(self.root))

    def test_script_checkout_prerequisite_is_reported(self):
        skill = self.skill()
        (skill / "setup.sh").write_text("#!/bin/sh\ngh repo clone ob-labs/ai-vision-ob\n")
        self.assertTrue(validate_catalog(self.root))

    def test_provenance_links_and_explicit_prose_are_allowed(self):
        self.skill(body=(
            "Never require a private ai-vision-ob checkout.\n"
            "[Provenance](https://github.com/ob-labs/ai-vision-ob/commit/123)\n"
            "[Section](#usage) [Email](mailto:example@example.com)\n"
            "```sh\nAIV_REPOSITORY=ob-labs/ai-vision-ob\n"
            "gh release download v1.0 --repo ob-labs/ai-vision-ob\n```"
        ))
        self.assertEqual(validate_catalog(self.root), [])


class InstallationChecksTests(unittest.TestCase):
    def test_missing_discovered_catalog_entry_fails(self):
        from scripts.check_installation import check_discovered_names
        with self.assertRaises(ValueError):
            check_discovered_names({"aivision-deploy"}, {"aivision-deploy", "aivision-trace"})

    def test_new_discovered_skill_is_allowed_and_required(self):
        from scripts.check_installation import check_discovered_names
        names = {"aivision-deploy", "aivision-metric", "aivision-quickstart", "aivision-trace", "new-skill"}
        self.assertIsNone(check_discovered_names(names, names))
        with self.assertRaises(ValueError):
            check_discovered_names(names - {"new-skill"}, names)

    def test_missing_initial_skill_fails_even_if_cli_omits_it(self):
        from scripts.check_installation import check_discovered_names
        names = {"aivision-deploy", "aivision-metric", "aivision-trace"}
        with self.assertRaises(ValueError):
            check_discovered_names(names, names)

    def test_changed_installed_resource_fails(self):
        from scripts.check_installation import check_copied_resources
        with tempfile.TemporaryDirectory() as temporary:
            source, installed = Path(temporary) / "source", Path(temporary) / "installed"
            source.mkdir()
            installed.mkdir()
            (source / "SKILL.md").write_text("original")
            (installed / "SKILL.md").write_text("changed")
            with self.assertRaises(ValueError):
                check_copied_resources(source, installed)

    def test_complete_copy_passes_and_missing_file_fails(self):
        from scripts.check_installation import check_copied_resources
        with tempfile.TemporaryDirectory() as temporary:
            source, installed = Path(temporary) / "source", Path(temporary) / "installed"
            for directory in (source, installed):
                (directory / "reference").mkdir(parents=True)
                (directory / "SKILL.md").write_text("original")
                (directory / "reference/guide.md").write_text("guide")
            self.assertIsNone(check_copied_resources(source, installed))
            (installed / "reference/guide.md").unlink()
            with self.assertRaises(ValueError):
                check_copied_resources(source, installed)


if __name__ == "__main__":
    unittest.main()
