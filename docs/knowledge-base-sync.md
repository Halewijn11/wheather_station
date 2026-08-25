# Knowledge Base Sync

KB repo: https://github.com/Halewijn11/knowledge_base

## Setup (done once, 2026-08-13)

```bash
# clone KB into project, strip its version history (not tracked as submodule/nested repo)
git clone https://github.com/Halewijn11/knowledge_base.git knowledge_base
rm -rf knowledge_base/.git

# stop tracking old local skills dir, replace with junction into KB's skills
git rm -r --cached .claude/skills
rm -rf .claude/skills
```

```powershell
cmd /c mklink /J "C:\PlatformIO\Projects\wheather_station\.claude\skills" "C:\PlatformIO\Projects\wheather_station\knowledge_base\.claude\skills"
```

`.gitignore` additions:
```
knowledge_base/
.claude/skills
```

## Result

- `knowledge_base/` — full KB clone (no `.git`, not versioned in this repo)
- `.claude/skills` — NTFS junction -> `knowledge_base/.claude/skills` (skills always match KB)

## Re-sync later

```bash
cd knowledge_base_source_elsewhere_or_reclone
```
To update KB content: delete `knowledge_base/`, re-clone, strip `.git` again (junction target path stays same, so junction keeps working automatically once folder exists again). Or, if want live updates, could instead `git pull` inside a real (non-stripped) clone — tradeoff: history stays on disk.
