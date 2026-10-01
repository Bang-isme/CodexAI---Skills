from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = SKILLS_ROOT / ".system" / "skill-capabilities.json"
MANIFEST_PATH = SKILLS_ROOT / ".system" / "manifest.json"


def read_frontmatter(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s|\Z)", content, re.DOTALL)
    if not match:
        raise AssertionError(f"missing YAML frontmatter: {path.relative_to(SKILLS_ROOT)}")
    return match.group(1)


class SkillCapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_capability_entries_match_manifest_skills(self) -> None:
        expected = set(self.manifest.get("skills", []))
        actual = {item.get("skill") for item in self.matrix.get("capabilities", [])}
        self.assertEqual(actual, expected)

    def test_skill_frontmatter_matches_capability_names(self) -> None:
        for item in self.matrix.get("capabilities", []):
            skill = item["skill"]
            skill_file = SKILLS_ROOT / skill / "SKILL.md"
            frontmatter = read_frontmatter(skill_file)
            name = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+)", frontmatter)
            description = re.search(r"(?m)^description:\s*(\S.*)$", frontmatter)
            with self.subTest(skill=skill):
                self.assertIsNotNone(name, f"{skill}: missing name")
                self.assertEqual(name.group(1).strip(), skill)
                self.assertIsNotNone(description, f"{skill}: missing description")

    def test_declared_resources_exist_inside_their_skill(self) -> None:
        resource_fields = ("scripts", "references", "assets", "agents", "templates", "starters")
        for item in self.matrix.get("capabilities", []):
            skill_root = (SKILLS_ROOT / item["skill"]).resolve()
            for field in resource_fields:
                for resource in item.get("resources", {}).get(field, []):
                    candidate = (skill_root / resource).resolve()
                    with self.subTest(skill=item["skill"], field=field, resource=resource):
                        self.assertTrue(
                            candidate == skill_root or skill_root in candidate.parents,
                            "declared resource escapes its skill directory",
                        )
                        self.assertTrue(candidate.exists(), "declared resource does not exist")

    def test_verification_owners_are_real_files(self) -> None:
        owners = [
            item.get("verification", {}).get("owner")
            for item in self.matrix.get("capabilities", [])
        ]
        owners.extend(
            item.get("verification", {}).get("owner")
            for item in self.matrix.get("shared_components", [])
        )
        for owner in owners:
            with self.subTest(owner=owner):
                self.assertIsInstance(owner, str)
                self.assertTrue((SKILLS_ROOT / owner).is_file())


if __name__ == "__main__":
    unittest.main()
