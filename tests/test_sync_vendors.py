"""Tests for agentic/scripts/sync_vendors.py, run against a temporary repo root."""

import json
from pathlib import Path

import pytest
import sync_vendors as s

SKILL_MD = "---\nname: {name}\ndescription: test skill\n---\n# {name}\n"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(s, "SKILLS_ROOT", tmp_path / "agentic" / "skills")
    return tmp_path


def add_skill(repo: Path, name: str, category: str = "core", text: str | None = None) -> Path:
    skill_dir = repo / "agentic" / "skills" / category / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(text if text is not None else SKILL_MD.format(name=name))
    return skill_dir


def sync(target: Path, mode: str = "symlink", render=None, apply: bool = True, force: bool = False):
    skills, errors = s.discover_skills()
    assert not errors
    return s.sync_dir(target, mode, render, skills, apply, force)


def managed(target: Path) -> list[str]:
    return json.loads((target / s.MANIFEST).read_text())["managed"]


# Discovery and frontmatter


def test_discover_drops_category_and_skips_nested_skill(repo):
    skill_dir = add_skill(repo, "do-thing")
    (skill_dir / "assets" / "inner").mkdir(parents=True)
    (skill_dir / "assets" / "inner" / "SKILL.md").write_text("nested asset")
    skills, errors = s.discover_skills()
    assert errors == []
    assert [(x.name, x.path) for x in skills] == [("do-thing", skill_dir)]


def test_duplicate_names_are_errors_and_excluded(repo):
    add_skill(repo, "do-thing", "core")
    add_skill(repo, "do-thing", "factory")
    skills, errors = s.discover_skills()
    assert skills == []
    assert len(errors) == 1 and "duplicate skill name 'do-thing'" in errors[0]


def test_parse_frontmatter_flattens_nested_keys():
    text = "---\nname: a\n# comment: x\nmetadata:\n  owner: 'me'\n---\nbody: no\n"
    assert s.parse_frontmatter(text) == {"name": "a", "metadata": "", "metadata.owner": "me"}


def test_frontmatter_warnings(repo):
    add_skill(repo, "no-name", text="---\ndescription: d\n---\n")
    add_skill(repo, "other-name", text="---\nname: wrong\n---\n")
    add_skill(repo, "good-name")
    skills, _ = s.discover_skills()
    warnings = s.frontmatter_warnings(skills)
    assert len(warnings) == 2
    assert "no-name: SKILL.md has no 'name:' field" in warnings
    assert "other-name: frontmatter name 'wrong' differs from folder name" in warnings


# OpenCode fields


def has_opencode_fields(text: str) -> bool:
    fields = s.parse_frontmatter(text)
    return all(fields.get(key, "").lower() == want for key, want in s.OPENCODE_FIELDS.items())


@pytest.mark.parametrize(
    "text",
    [
        "---\nname: a\ndescription: d\n---\n# A\n",
        "---\nname: a\nmetadata:\n  owner: x\n---\nbody\n",
        "---\nname: a\ncompatibility: opencode\nmetadata:\n  opencode/slash: 'true'\n---\n",
        "# no frontmatter\n",
        "---\nname: a\n---",
    ],
    ids=["plain", "existing-metadata", "partial", "no-frontmatter", "no-trailing-newline"],
)
def test_add_opencode_fields_adds_missing_and_is_idempotent(text):
    out = s.add_opencode_fields(text)
    assert has_opencode_fields(out)
    assert s.add_opencode_fields(out) == out


def test_add_opencode_fields_keeps_existing_metadata_and_body():
    out = s.add_opencode_fields("---\nname: a\nmetadata:\n  owner: x\n---\nbody\n")
    assert s.parse_frontmatter(out)["metadata.owner"] == "x"
    assert out.count("metadata:") == 1
    assert out.endswith("---\nbody\n")


def test_add_opencode_fields_leaves_complete_text_unchanged():
    text = (
        "---\nname: a\ncompatibility: opencode\nmetadata:\n  opencode/slash: true\n  opencode/autoinvoke: true\n---\n"
    )
    assert s.add_opencode_fields(text) == text


def test_add_opencode_fields_rejects_unterminated_frontmatter():
    with pytest.raises(ValueError, match="no closing"):
        s.add_opencode_fields("---\nname: a\n")


def test_opencode_warnings_only_for_conflicting_values(repo):
    add_skill(repo, "missing-fields")
    add_skill(repo, "wrong-value", text="---\nname: wrong-value\ncompatibility: claude\n---\n")
    skills, _ = s.discover_skills()
    assert s.opencode_warnings(skills) == [
        "wrong-value: frontmatter compatibility is 'claude', opencode needs 'opencode'"
    ]


# Syncing a vendor folder


def test_symlink_add_then_up_to_date(repo):
    skill_dir = add_skill(repo, "do-thing")
    target = repo / ".claude" / "skills"
    assert sync(target) == (1, 0)
    link = target / "do-thing"
    assert link.is_symlink() and link.resolve() == skill_dir.resolve()
    assert not Path(link.readlink()).is_absolute()  # relative inside the repo
    assert managed(target) == ["do-thing"]
    assert sync(target) == (0, 0)


def test_dry_run_changes_nothing(repo):
    add_skill(repo, "do-thing")
    target = repo / ".claude" / "skills"
    assert sync(target, apply=False) == (1, 0)
    assert not target.exists()


def test_copy_detects_edits(repo):
    skill_dir = add_skill(repo, "do-thing")
    target = repo / ".agents" / "skills"
    assert sync(target, mode="copy") == (1, 0)
    copied = target / "do-thing"
    assert copied.is_dir() and not copied.is_symlink()
    assert sync(target, mode="copy") == (0, 0)
    (skill_dir / "SKILL.md").write_text(SKILL_MD.format(name="do-thing") + "more\n")
    assert sync(target, mode="copy") == (1, 0)
    assert (copied / "SKILL.md").read_text().endswith("more\n")


def test_switching_mode_updates_managed_skill(repo):
    add_skill(repo, "do-thing")
    target = repo / ".claude" / "skills"
    sync(target)
    assert sync(target, mode="copy") == (1, 0)
    assert not (target / "do-thing").is_symlink()


def test_render_writes_fields_without_touching_source(repo):
    skill_dir = add_skill(repo, "do-thing")
    source_text = (skill_dir / "SKILL.md").read_text()
    target = repo / ".opencode" / "skills"
    assert sync(target, mode="copy", render=s.add_opencode_fields) == (1, 0)
    assert has_opencode_fields((target / "do-thing" / "SKILL.md").read_text())
    assert (skill_dir / "SKILL.md").read_text() == source_text
    assert sync(target, mode="copy", render=s.add_opencode_fields) == (0, 0)


def test_render_replaces_symlinked_skill_md_instead_of_writing_through(repo):
    real = repo / "shared.md"
    real.write_text(SKILL_MD.format(name="do-thing"))
    skill_dir = add_skill(repo, "do-thing", text="")
    (skill_dir / "SKILL.md").unlink()
    (skill_dir / "SKILL.md").symlink_to(real)
    target = repo / ".opencode" / "skills"
    sync(target, mode="copy", render=s.add_opencode_fields)
    rendered = target / "do-thing" / "SKILL.md"
    assert not rendered.is_symlink() and has_opencode_fields(rendered.read_text())
    assert real.read_text() == SKILL_MD.format(name="do-thing")


def test_unmanaged_entry_is_conflict_unless_forced(repo):
    add_skill(repo, "do-thing")
    target = repo / ".claude" / "skills"
    (target / "do-thing").mkdir(parents=True)
    (target / "do-thing" / "SKILL.md").write_text("vendor's own")
    assert sync(target) == (0, 1)
    assert (target / "do-thing" / "SKILL.md").read_text() == "vendor's own"
    assert sync(target, force=True) == (1, 0)
    assert (target / "do-thing").is_symlink()
    assert managed(target) == ["do-thing"]


def test_prune_removes_only_managed_skills(repo):
    skill_dir = add_skill(repo, "do-thing")
    target = repo / ".claude" / "skills"
    sync(target)
    (target / "vendor-skill").mkdir()
    (skill_dir / "SKILL.md").unlink()
    skill_dir.rmdir()
    assert sync(target) == (1, 0)
    assert not (target / "do-thing").exists() and not (target / "do-thing").is_symlink()
    assert (target / "vendor-skill").is_dir()
    assert managed(target) == []


# Command line


def run(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr("sys.argv", ["sync_vendors.py", *argv])
    return s.main()


def test_main_check_exits_1_when_out_of_sync_then_0(repo, monkeypatch):
    add_skill(repo, "do-thing")
    assert run(monkeypatch, "claude", "--check") == 1
    assert run(monkeypatch, "claude") == 0
    assert run(monkeypatch, "claude", "--check") == 0


def test_main_opencode_always_copies_with_fields(repo, monkeypatch):
    add_skill(repo, "do-thing")
    assert run(monkeypatch, "opencode") == 0
    synced = repo / ".opencode" / "skills" / "do-thing"
    assert synced.is_dir() and not synced.is_symlink()
    assert has_opencode_fields((synced / "SKILL.md").read_text())
    assert run(monkeypatch, "opencode", "--check") == 0


def test_main_check_exits_1_on_conflicting_opencode_field(repo, monkeypatch):
    add_skill(repo, "do-thing", text="---\nname: do-thing\ncompatibility: claude\n---\n")
    assert run(monkeypatch, "opencode") == 0
    assert run(monkeypatch, "opencode", "--check") == 1


def test_main_refuses_duplicate_names(repo, monkeypatch, capsys):
    add_skill(repo, "do-thing", "core")
    add_skill(repo, "do-thing", "engineering")
    assert run(monkeypatch, "claude") == 1
    assert "Skills not synced" in capsys.readouterr().err
    assert not (repo / ".claude" / "skills").exists()


def test_main_exits_1_on_conflict(repo, monkeypatch):
    add_skill(repo, "do-thing")
    (repo / ".claude" / "skills" / "do-thing").mkdir(parents=True)
    assert run(monkeypatch, "claude") == 1


def test_main_only_skills_matches_default(repo, monkeypatch):
    add_skill(repo, "do-thing")
    assert run(monkeypatch, "claude", "--only", "skills", "--check") == 1
    assert run(monkeypatch, "claude", "--only", "skills") == 0
    assert run(monkeypatch, "claude", "--check") == 0


def test_main_rejects_unknown_kind(repo, monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, "claude", "--only", "hooks")
