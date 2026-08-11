from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "table-proof"
SKILL_FILE = SKILL_DIR / "SKILL.md"


class AgentSkillTests(unittest.TestCase):
    def test_open_standard_frontmatter(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match)

        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            key, separator, value = line.partition(":")
            self.assertEqual(separator, ":", line)
            fields[key.strip()] = value.strip()

        self.assertEqual(fields["name"], SKILL_DIR.name)
        self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertIn("Use when", fields["description"])
        self.assertLessEqual(len(fields["description"]), 1024)

    def test_relative_skill_references_exist(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        self.assertTrue(targets)

        for target in targets:
            with self.subTest(target=target):
                self.assertFalse(target.startswith(("http://", "https://")))
                self.assertTrue((SKILL_DIR / target).is_file())

    def test_portable_core_stays_small(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 120)
        self.assertNotIn("OpenAI API", text)


if __name__ == "__main__":
    unittest.main()
