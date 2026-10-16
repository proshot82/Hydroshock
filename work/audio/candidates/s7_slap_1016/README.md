# Звуковой пакет З7 — «хлоп» ладонью по папке (кандидаты, 16.10.2026)

Разбор автора 16.10.2026: когда Лапидус пытается поднять папку со стойки (Z04), на неё ложится рука Изольды со звуком «ХЛОП». Картинка — `work/higgsfield/candidates/act2_fix_1016/` (`z04_slap__a/b`).

**В `assets/` ничего не перенесено — только после выбора автора.** Имя в игре — `sfx_folder_slap.ogg`.

| Файл | Исходник |
|---|---|
| `final/sfx_folder_slap_1.ogg` | `raw/sfx_folder_slap_1.mp3` |
| `final/sfx_folder_slap_2.ogg` | `raw/sfx_folder_slap_2.mp3` |
| `final/sfx_folder_slap_3.ogg` | `raw/sfx_folder_slap_3.mp3` |

**Из чего:** ElevenLabs Sound Effects (`tools/audio/eleven.py sfx --sec 1 --influence 0.6`), промпт: «a single sharp flat-palm slap of a hand on a thick cardboard folder lying on a marble reception counter, crisp loud smack, short, dry, no voice, no music»; журнал — `work/elevenlabs/log.jsonl`. Доводка — `tools/audio/finish.py --max 0.8 --fade 0.15 --lufs -16 --mono` (пик −1,5 dBFS; короткий щелчок упирается в пик раньше, чем в громкость, поэтому −26 LUFS). У варианта 1 удар начинается позже (≈0,29 с), у 2 и 3 — сразу.

Условия ElevenLabs — как у пакетов З2–З4 (`assets/audio/SOURCES.md`).
