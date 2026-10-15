import logging
import subprocess
from pathlib import Path

from repoharvester import collect_files, get_repo_name, harvest, main, remove_comments


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

    out = harvest(str(src), tmp_path / 'out', strip_comments=True)
    assert out.read_text() == '## proj\n### pkg/a.py\na = 1  \n\n### end of file\n'
    assert (tmp_path / 'out' / 'skipped_files.txt').read_text() == 'bad.txt\n'


def test_remove_comments_edge_cases():
    assert remove_comments('s = """\nSELECT 1 # x\n"""  # c\n', 'py') == 's = """\nSELECT 1 # x\n"""  \n'
    assert remove_comments('echo ${#arr[@]} # c\n', 'sh') == 'echo ${#arr[@]} \n'
    assert remove_comments('url: http://x/#frag\n', 'yaml') == 'url: http://x/#frag\n'
    assert remove_comments('a { b: url(http://x.com/a.png); } /* c */', 'scss') == 'a { b: url(http://x.com/a.png); } '
    assert remove_comments('s = [[ a -- b ]] -- c\n--[==[ long\n]==]x', 'lua') == 's = [[ a -- b ]] \nx'


def test_output_dir_inside_source_is_not_harvested(tmp_path: Path):
    (tmp_path / 'a.txt').write_text('a')
    harvest(str(tmp_path), tmp_path / 'output')
    out = harvest(str(tmp_path), tmp_path / 'output')
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

    text = harvest(str(src), tmp_path / 'out').read_text()

    assert '### app.py' in text
    assert '### new.py' in text
    assert 'dist/bundle.js' not in text
    assert '### .env' not in text
    assert 'SECRET' not in text


def test_harvest_logs_token_estimate(tmp_path: Path, caplog):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'a.txt').write_text('x' * 4000)
    with caplog.at_level(logging.INFO, logger='repoharvester'):
        harvest(str(tmp_path / 'src'), tmp_path / 'out')
    assert '~1.0k tokens' in caplog.text
