# Латунный янычар: Гидроудар (BJ3)
Язык: всё по-русски. Автор — Lao, не программист; технические шаги ему — пошагово.
Действующие документы (иерархия при конфликте):
  docs/DESIGN_BIBLE.md, docs/02_WRITING_BIBLE.md, docs/BJ3_WORLD_CANON_V2.md
  → docs/BJ3_PUZZLE_CHAIN_PROMPT_V2.md → docs/BJ3_SKELETON_S3.md (утверждён 14.08.2026, md5 600a74d61d3aa00c8a9cad80711f2858).
Конфликт — доложить автору, не решать молча.
docs/history/ (PUZZLE_FREE, промпт v1, handoff ChatGPT, Фаза_0.docx, v0.8, v1.1.2) — не источник.
Текущая точка — BJ3_HANDOFF.md и PROJECT_STATUS_HYDROUDAR.md. Фаза 2 закрыта: четыре акта заморожены (сдачи acts/act*/ACT*_SUBMISSION.md побеждают скелет письменным решением автора).
Производственная сводка — docs/BJ3_GDD.md и docs/BJ3_SLOT_FLAGS.md (проверка: python tools/texts/check_slot_flags.py); тексты — texts/act*/ACT*_TEXTS_FINAL.md (генерируются tools/texts/merge_texts.py, правки через texts/polish/ACT*_TEXTS_EDITS.md), проверка tools/texts/check_texts.py.
Инфраструктура скопирована из BJ2 (C:\Янычар\bj2) — сам BJ2 не трогать.
Спойлер-гигиены нет. Генерируемые данные руками не править. Релиз — только по слову «собирай».
Новая сессия (заговорил о ней автор или Claude) — сначала проверить, нужно ли слияние в main (открытые PR, отставание main), и доложить автору (решение автора 08.10.2026).
