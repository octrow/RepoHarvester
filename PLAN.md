# План: RepoHarvester

Открытые баги, планы и идеи. Дата: 2026-11-05. Закрытый пункт удаляется или получает ✅ со ссылкой на коммит.

Источники: [логические находки](docs/plans/2026-11-05-logic-map-fixes.md) (#N), [system design](docs/system-design.md) (Risks), GitHub issues.

## Баги

HIGH-находок нет.

MEDIUM:
- [ ] #1 Dotfile (`.env`, `.DS_Store`) не матчится по `Path.suffix`; `.env` из не-git папки попадает в вывод с секретами ([план #1](docs/plans/2026-11-05-logic-map-fixes.md))
- [ ] #8 `_remove_python_comments` сдвигает строки из-за `splitlines()` (`\x0c` и т.п.): код уезжает в комментарий ([план #8](docs/plans/2026-11-05-logic-map-fixes.md))
- [ ] #9 `_drop_git_ignored` молча теряет файлы вложенного репо/сабмодуля (вопрос владельцу; минимум лог) ([план #9](docs/plans/2026-11-05-logic-map-fixes.md))
- [x] ✅ 2026-11-05 Вывод пишется через temp-файл + `os.replace` (`_write_atomic`), тест `test_interrupted_write_keeps_previous_output`; не закоммичено
- [ ] Частично ✅ 2026-11-05: `git clone` получил общий дедлайн `CLONE_TIMEOUT_S`=600 с (`CloneError`, тест `test_clone_times_out`; не закоммичено); осталось: `git ls-files` без таймаута, флаг `--timeout`. Было: нет таймаута на `git clone` и `git ls-files`: недоступный remote вешает CLI (`repoharvester.py:264-271`, `:216`, [Risks](docs/system-design.md#risks))
- [ ] Нет лимита на общий размер, в RAM ~3 копии текста (`repoharvester.py:174`, `:211`, `:316`, [Risks](docs/system-design.md#risks))

LOW (детали в [плане](docs/plans/2026-11-05-logic-map-fixes.md)):
- [ ] #2 нет `git` → traceback вместо `CloneError`
- [ ] #3 `skipped_files.txt` и `<name>_all_files.txt` перезаписываются при двух репо в один `output/`
- [ ] #4 WARNING о размере выводится до применения globs и git-ignore
- [ ] #5 GUI Cancel не работает для локальной папки и после клона
- [ ] #6 нет `--` перед `repo` в `git clone`
- [ ] #10 старые `*_all_files.txt` попадают во вход при `-o -` или другом `-o`
- [ ] #11 `start_new_session=True` лишает git терминала: нет запроса пароля в CLI (не подтверждено)
- [ ] #12 Ctrl+C или закрытие GUI не останавливает git
- [ ] #13 FIFO в не-git папке вешает `read_text`
- [ ] #7 закрыт ревью как не баг (оставить как есть)
- [ ] [GitHub #9](https://github.com/octrow/RepoHarvester/issues/9): жалоба, что краулер с user agent `RepoHarvester/1.2.` грузит чужой GitLab и не уважает robots.txt; выяснить, наш ли это агент

## Планы и фичи

- [ ] Порядок работ: #1 и #8 с тестами, затем #9, затем #2/#6/#11/#12 (процесс клона), затем #3/#4/#5/#10/#13 ([план, Order of work](docs/plans/2026-11-05-logic-map-fixes.md))
- [ ] Закрыть каждую находку ✅ или решением "оставить" с причиной; Known gaps в карте перечисляет все открытые HIGH и MEDIUM ([Done when](docs/plans/2026-11-05-logic-map-fixes.md))
- [ ] Флаг `--timeout` и `timeout=` в `subprocess.run` ([Risks](docs/system-design.md#risks))
- [ ] Флаг `--max-total-mb`: остановка с понятной ошибкой до render ([Risks](docs/system-design.md#risks))
- [x] ✅ 2026-11-05 Атомарная запись: temp-файл рядом + `os.replace`; не закоммичено

## Идеи

- [ ] Потоковая запись при пике >500 MB RSS или выводе больше контекста модели (~1 M токенов) ([system-design](docs/system-design.md), Next rung)
- [ ] Таймауты обязательны при первом запуске без присмотра (CI, сервис) ([system-design](docs/system-design.md), Next rung)
- [ ] Кэш: постоянный bare-клон по URL + `git fetch --depth 1`, если один репо собирают часто ([system-design](docs/system-design.md), раздел 5)
- [ ] LOW: `ls-files` читается целиком в `set`, важно только для монорепо ([Risks](docs/system-design.md#risks))
- [ ] LOW: оценка токенов `len/4` не бюджет, не использовать для гейтинга LLM-вызовов ([Risks](docs/system-design.md#risks))

## Подробные планы

- [docs/plans/2026-11-05-logic-map-fixes.md](docs/plans/2026-11-05-logic-map-fixes.md): находки #1-#13 по логике
- [docs/logic-map.md](docs/logic-map.md): карта логики, Known gaps
- [docs/system-design.md](docs/system-design.md): system design, расчёт нагрузки, отказы, риски
- Сводка по всем репо: `~/dev/docs/system-design-report-2026-11-05.md`
