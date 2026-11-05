# Plan: logic map findings

Findings from writing `docs/logic-map.md` on 2026-11-05. An independent review ran the same day: it checked #1–#7, changed #5, #6 and #7, and added #8–#13.
The map describes the code as it is; this file says what is wrong with it and what we propose. New findings are appended.
A fixed finding gets ✅ and the map is updated in the same commit.

Severity: HIGH: wrong result for the user. MEDIUM: worse result than it could be. LOW: noise, debt, docs.
"Question": not sure if bug or intent; the owner decides. "Not confirmed": needs a live run.

## Findings

| # | Map step | What is wrong | We propose | Severity |
|---|---|---|---|---|
| 1 | 4 | Extension is `Path.suffix` (`repoharvester.py:152`), empty for `.env`, `.DS_Store`. Group `system` lists `ds_store` and `certificate` lists `key`, but dotfiles never match. A `.env` in a non-git local folder (git filter fails open, `:217`) is put into the output with its secrets. | Match dotfile names (`.env*`, `.DS_Store`) as exact names in `FILENAME_GROUPS`; decide whether `.env` is a skip group | MEDIUM |
| 2 | 3, 5 | `git` missing: `subprocess.Popen` (`:263`) and `subprocess.run` (`:215`) raise `FileNotFoundError`; CLI catches only `CloneError` (`:360`), so the user sees a traceback. Local folders also need git for step 5. | Treat missing git as `CloneError` in clone; in `_drop_git_ignored` fail open on `FileNotFoundError` | LOW |
| 3 | 8 | `skipped_files.txt` has a fixed name and `<name>_all_files.txt` depends only on the folder/repo name (`:296-299`): harvesting two repos into one `output/` loses the first skip list; equal names overwrite. | Question: prefix skip list with the repo name, or accept and document | LOW |
| 4 | 4, 5 | `_within_size` logs its WARNING in `collect_files` (`:155`) before globs and git-ignore run (`:226-228`): large ignored or glob-excluded files still warn "Skipping". | Move the size check after selection, or accept | LOW |
| 5 | Side flow GUI | Cancel is read only inside `_clone` (`:269`). For a local folder, or a git source whose clone already finished, the button shows "Cancelling…" until the harvest finishes and then reports success. | Check the event between files in `_render`, or hide Cancel for local folders | LOW |
| 6 | 2, 3 | `repo` goes to `git clone` with no `--` (`:262`). A value like `--upload-pack=...` is read as an option. Review: with one injected argument the temp dir becomes the source and git fails with "repository ... does not exist" (tried `--upload-pack=` and `--config=core.sshCommand=`; nothing ran), and `ext::` is off by default. Practical effect is a confusing error. | Add `--` before `repo` anyway (one token, defence in depth) | LOW (was MEDIUM) |
| 7 | 3 | `_kill_tree` (`:254`) calls `os.killpg` on a process that may have just exited. Review: the child is not reaped before `communicate`/`wait`, and `killpg` on a zombie group leader succeeds (checked on Linux), so `ProcessLookupError` does not happen. | Close: keep as is | not a bug |
| 8 | 6 | `_remove_python_comments` (`:87`) applies tokenizer rows to `content.splitlines()`, which also splits on `\x0c`, `\x1c`–`\x1e`, `\x85`, ` `, ` `; the tokenizer splits only on `\n`. Rows shift: comments stay, or columns are cut from the wrong line. Checked: `s = 'a b'  # c1\nt = 3  # c2\n` → `s = 'a b'  # ct = 3  # c2\n` (code moved into a comment). | Split with `io.StringIO(content).readlines()` (same lines as the tokenizer); add a test with `\x0c` and ` ` | MEDIUM |
| 9 | 5 | `_drop_git_ignored` (`:215-220`) keeps only paths git lists. A nested git repo or a checked-out submodule is listed as one `inner/` entry (checked), so all its files are dropped without a log line. | Question: list with `--recurse-submodules` (cannot combine with `--others`) or keep files under a listed `dir/` entry; at least log how many files git dropped | MEDIUM |
| 10 | 5 | The output-folder filter (`:225-226`) covers only the current `output_dir`. With `-o -` (stdout) or another `-o`, an old `output/*_all_files.txt` inside the harvested folder is included when the folder is not a git repo or `output/` is not git-ignored. | Also drop files named `*_all_files.txt` / `skipped_files.txt`, or always drop `DEFAULT_OUTPUT_DIR` under root | LOW |
| 11 | 3 | `start_new_session=True` (`:263`) leaves git without a controlling terminal (checked: `/dev/tty` gives "No such device or address"). In the CLI, an HTTPS repo that needs a typed password, an unknown SSH host key or a key passphrase fails instead of prompting. Not confirmed with a real remote. | Use the new session only when a cancel event is given (GUI), or document that a credential helper / ssh-agent is needed | LOW |
| 12 | 3 | Interrupting the run does not stop git: Ctrl+C in the CLI does not reach the new session, and `Popen.__exit__` on `KeyboardInterrupt` neither waits nor kills; closing the GUI kills only the daemon worker. git keeps cloning detached while the temp dir is removed. A leftover temp dir is not confirmed. | `try/except BaseException: _kill_tree(proc); raise` in `_clone`; on GUI close, set the cancel event and wait briefly | LOW |
| 13 | 4, 6 | A FIFO in a non-git local folder passes step 4 (not a symlink, size 0) and `read_text` (`:173`) blocks forever. git does not list non-regular files, so git folders are safe. | Keep only `path.is_file()` in `collect_files` | LOW |

## Order of work

1. #1 and #8 (secrets in output; code corrupted by `-r`), with tests.
2. #9 (owner decides; at least a log line).
3. #2, #6, #11, #12 (clone process handling, one function).
4. #3, #4, #5, #10, #13 (decisions and polish). #7 closed by review.

## Done when

- [ ] every finding has ✅ or a "keep as is" decision with a reason;
- [ ] Known gaps in the map lists every open HIGH and MEDIUM finding.
