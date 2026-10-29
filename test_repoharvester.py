import io
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from repoharvester import (
    CloneError,
    HarvestCancelled,
    HarvestOptions,
    collect_files,
    get_repo_name,
    harvest,
    harvest_text,
    main,
    remove_comments,
)


def test_remove_comments_keeps_strings():
    assert remove_comments('x = "#fff"  # note\n', 'py') == 'x = "#fff"  \n'
    assert remove_comments('u = "http://a"; /* c */ // d\n', 'js') == 'u = "http://a";  \n'
    assert remove_comments('<a/><!-- c -->', 'html') == '<a/>'
    assert remove_comments('# kept', 'md') == '# kept'


def test_get_repo_name():
    assert get_repo_name('git@github.com:user/proj.git') == 'proj'
    assert get_repo_name('https://github.com/user/proj/') == 'proj'


def test_harvest_local_folder(tmp_path: Path):
    src = tmp_path / 'proj'
    (src / 'node_modules').mkdir(parents=True)
    (src / 'node_modules' / 'x.js').write_text('nope')
    (src / 'pkg').mkdir()
    (src / 'pkg' / 'a.py').write_text('a = 1  # c\n')
    (src / 'logo.PNG').write_bytes(b'\x89PNG')
    (src / 'package-lock.json').write_text('{}')
    (src / 'bad.txt').write_bytes(b'\xff\xfe')

    assert [p.name for p in collect_files(src)] == ['bad.txt', 'a.py']

    out = harvest(str(src), HarvestOptions(tmp_path / 'out', strip_comments=True))
    assert out.read_text() == (
        '## proj\n'
        '### Files: 1, ~10 tokens\n'
        'pkg/a.py  ~10\n'
        '\n'
        '### pkg/a.py\na = 1  \n\n### end of file\n'
    )
    assert (tmp_path / 'out' / 'skipped_files.txt').read_text() == 'bad.txt\n'


def test_remove_comments_edge_cases():
    assert remove_comments('s = """\nSELECT 1 # x\n"""  # c\n', 'py') == 's = """\nSELECT 1 # x\n"""  \n'
    assert remove_comments('echo ${#arr[@]} # c\n', 'sh') == 'echo ${#arr[@]} \n'
    assert remove_comments('url: http://x/#frag\n', 'yaml') == 'url: http://x/#frag\n'
    assert remove_comments('a { b: url(http://x.com/a.png); } /* c */', 'scss') == 'a { b: url(http://x.com/a.png); } '
    assert remove_comments('s = [[ a -- b ]] -- c\n--[==[ long\n]==]x', 'lua') == 's = [[ a -- b ]] \nx'


def test_output_dir_inside_source_is_not_harvested(tmp_path: Path):
    (tmp_path / 'a.txt').write_text('a')
    harvest(str(tmp_path), HarvestOptions(tmp_path / 'output'))
    out = harvest(str(tmp_path), HarvestOptions(tmp_path / 'output'))
    assert '### output/' not in out.read_text()


def test_cli_lists_do_not_swallow_repo(tmp_path: Path):
    (tmp_path / 'src' / 'docs').mkdir(parents=True)
    (tmp_path / 'src' / 'docs' / 'd.txt').write_text('d')
    (tmp_path / 'src' / 'k.txt').write_text('k')
    main(['--exclude', 'docs,vendor', '--no-skip', 'media', str(tmp_path / 'src'), '-o', str(tmp_path / 'o')])
    harvested = (tmp_path / 'o' / 'src_all_files.txt').read_text()
    assert '### k.txt' in harvested
    assert 'd.txt' not in harvested


def test_git_repo_respects_gitignore(tmp_path: Path):
    src = tmp_path / 'proj'
    (src / 'dist').mkdir(parents=True)
    (src / 'dist' / 'bundle.js').write_text('built')
    (src / '.env').write_text('SECRET=1')
    (src / '.gitignore').write_text('dist/\n.env\n')
    (src / 'app.py').write_text('x = 1\n')
    (src / 'new.py').write_text('untracked but not ignored\n')
    subprocess.run(['git', 'init', '-q', str(src)], check=True)
    subprocess.run(['git', '-C', str(src), 'add', 'app.py', '.gitignore'], check=True)

    text = harvest(str(src), HarvestOptions(tmp_path / 'out')).read_text()

    assert '### app.py' in text
    assert '### new.py' in text
    assert 'dist/bundle.js' not in text
    assert '### .env' not in text
    assert 'SECRET' not in text


def test_harvest_logs_token_estimate(tmp_path: Path, caplog):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'a.txt').write_text('x' * 4000)
    with caplog.at_level(logging.INFO, logger='repoharvester'):
        harvest(str(tmp_path / 'src'), HarvestOptions(tmp_path / 'out'))
    assert '~1.0k tokens' in caplog.text


def test_python_comments_use_tokenizer():
    src = '#!/usr/bin/env python\nx = f"{a}#b"  # c\ns = """\n# kept\n"""\n'
    assert remove_comments(src, 'py') == '#!/usr/bin/env python\nx = f"{a}#b"  \ns = """\n# kept\n"""\n'
    assert remove_comments('x = (  # broken python\n', 'py') == 'x = (  \n'


def test_cancel_stops_a_hanging_clone(tmp_path: Path, monkeypatch):
    monkeypatch.setenv('GIT_SSH_COMMAND', 'sleep 30; true')
    cancel = threading.Event()
    threading.Timer(0.5, cancel.set).start()
    started = time.monotonic()
    with pytest.raises(HarvestCancelled):
        harvest('git@example.invalid:x/y.git', HarvestOptions(tmp_path / 'out'), cancel)
    assert time.monotonic() - started < 5


def test_failed_clone_keeps_previous_result(tmp_path: Path):
    previous = tmp_path / 'out' / 'y_all_files.txt'
    previous.parent.mkdir()
    previous.write_text('good result')
    with pytest.raises(CloneError, match=r'y\.git'):
        harvest(str(tmp_path / 'missing' / 'y.git'), HarvestOptions(tmp_path / 'out'))
    assert previous.read_text() == 'good result'


def _sample_repo(tmp_path: Path) -> Path:
    src = tmp_path / 'src'
    for rel in ('app.py', 'lib/util.py', 'tests/test_app.py', 'README.md', 'notes.txt'):
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(f'# {rel}\n')
    return src


def test_file_tree_lists_every_file_with_tokens(tmp_path: Path):
    text = harvest_text(str(_sample_repo(tmp_path))).text
    tree = text.split('\n\n', 1)[0].splitlines()
    assert tree[1].startswith('### Files: 5, ~')
    assert [line.split('  ~')[0] for line in tree[2:]] == [
        'README.md', 'app.py', 'notes.txt', 'lib/util.py', 'tests/test_app.py']


def test_include_and_exclude_globs(tmp_path: Path):
    options = HarvestOptions(include_globs=('*.py',), exclude_globs=('tests/*',))
    text = harvest_text(str(_sample_repo(tmp_path)), options).text
    assert '### app.py' in text
    assert '### lib/util.py' in text
    assert 'test_app.py' not in text
    assert 'README.md' not in text


def test_cli_writes_to_stdout(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main([str(_sample_repo(tmp_path)), '-o', '-', '--include', 'README.md'])
    out = capsys.readouterr().out
    assert out.startswith('## src\n### Files: 1, ~')
    assert '### README.md\n# README.md\n' in out
    assert not (tmp_path / 'output').exists()


def test_stdout_is_utf8_even_on_a_legacy_console(tmp_path: Path, monkeypatch):
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'notes.md').write_text('Привет 👋\n', encoding='utf-8')
    raw = io.BytesIO()
    monkeypatch.setattr(sys, 'stdout', io.TextIOWrapper(raw, encoding='cp1252'))  # Windows pipe default
    main([str(src), '-o', '-'])
    assert 'Привет 👋' in raw.getvalue().decode('utf-8')


def test_log_and_header_report_the_same_token_total(tmp_path: Path, caplog):
    src = tmp_path / 'src'
    src.mkdir()
    for i in range(30):
        (src / f'f{i:02}.txt').write_text('y' * 400)
    with caplog.at_level(logging.INFO, logger='repoharvester'):
        text = harvest_text(str(src)).text
    header_total = text.splitlines()[1].split('~')[1].split(' ')[0]
    assert f'~{header_total} tokens' in caplog.text


def test_python_comments_with_form_feed_line():
    src = 'x = 1\n\x0c\n# comment\ny = 2\n'
    assert remove_comments(src, 'py') == 'x = 1\n\x0c\n\ny = 2\n'


def test_ds_store_is_skipped_by_default(tmp_path: Path):
    src = tmp_path / 'src'
    src.mkdir()
    (src / '.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1')
    (src / 'a.txt').write_text('a')
    assert [p.name for p in collect_files(src)] == ['a.txt']
    assert [p.name for p in collect_files(src, HarvestOptions(skip_groups=frozenset()))] == ['.DS_Store', 'a.txt']
