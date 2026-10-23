#!/usr/bin/env python3
"""Манифест пакета З8 (Suno v6): для каждого из 78 звуков игры — стиль для Suno.

Музыка, стингеры, эффекты и амбиенты — тот же английский промпт, по которому сделан принятый
вариант (журнал work/elevenlabs/log.jsonl, пакеты З1–З7). Для эффектов и амбиентов к нему
добавлено «звук без музыки»: Suno — музыкальная модель, отдельного режима эффектов у неё нет.
Звуки, сделанные синтезом или взятые из BJ2, промпта не имели — описание по спеке §9.

  python work/audio/candidates/s8_suno_v6_1023/make_manifest.py  → manifest.json
"""
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LOG = [json.loads(l) for l in (ROOT / "work/elevenlabs/log.jsonl").open(encoding="utf-8")]
NAMES = sorted(p.stem for p in (ROOT / "assets/audio").glob("*.ogg"))

MUS_NEG = "vocals, singing, humming, choir, spoken word, lyrics"
SFX_TAIL = ("isolated sound effect only, realistic foley field recording, "
            "no music, no melody, no instruments, no beat, no rhythm, no vocals")
SFX_NEG = "music, melody, song, instruments, drums, beat, bass, synth, vocals, singing, choir"
AMB_TAIL = "ambient room tone soundscape only, no music, no melody, no instruments, no beat, no vocals, no speech"


def last_prompt(prefix):
    """Промпт последнего запроса к ElevenLabs, чей файл начинается с prefix."""
    hits = [d for d in LOG if os.path.basename(d.get("file", "")).startswith(prefix)]
    return hits[-1]["prompt"] if hits else None


# Принятые варианты, у которых имя исходника отличается от имени в игре (SOURCES.md, README пакетов)
MUSIC = {
    "bgm_title": (last_prompt("bgm_title_v25_1"), 90),
    "bgm_hotel": (last_prompt("bgm_hotel_v25_1"), 120),
    "bgm_service": (last_prompt("bgm_service_v25_1"), 120),
    "bgm_below": (last_prompt("bgm_below_v25_2"), 120),
    "bgm_deep": (last_prompt("bgm_deep_a"), 100),
    "bgm_epilogue": (last_prompt("bgm_finale_c4"), 120),
    "mus_hold": (last_prompt("mus_hold_v25_1"), 45),
    # пакет З6: композиционный план ElevenLabs сведён в одну строку стиля
    "bgm_resort": ("instrumental, quirky point-and-click adventure game soundtrack, clear hummable main melody, "
                   "warm vintage small live band recording, 84 BPM, 1960s soviet black-sea sanatorium estrada, "
                   "lazy seaside swing-waltz, accordion and mandolin play the melody, vibraphone, soft clarinet, "
                   "brushed snare, upright bass, sleepy sun-drenched holiday, major key, no vocals", 90),
    "bgm_hotel_tense": ("instrumental, quirky point-and-click adventure game soundtrack, 1960s soviet black-sea "
                        "sanatorium estrada band: accordion, mandolin, clarinet, upright bass, warm vintage small live "
                        "band recording, clearly in C minor, minor-key harmony throughout, 90 BPM, slow creeping "
                        "comedic suspense, walking pizzicato bass, accordion swells, muted trumpet wah-wah, ticking "
                        "clock, worried but funny, no vocals", 100),
    "sting_solved": (last_prompt("sting_solved_v25_1"), 10),
    "sting_relic": (last_prompt("sting_relic_v25_2"), 10),
    "sting_water": (last_prompt("sting_water_2"), 10),
}
MUS_NEG_EXTRA = {
    "bgm_resort": ", electronic beats, heavy drums, horror",
    "bgm_hotel_tense": ", electronic beats, heavy drums, horror, major key, carefree",
    "bgm_below": ", organ, march, church, fanfare",
    "bgm_deep": ", organ, church, march",
}

# Эффекты без своего запроса в журнале под игровым именем
SFX_OVERRIDE = {
    "sfx_shock_thud": last_prompt("sfx_shock_boom_1"),
    "sfx_crowd_part": last_prompt("sfx_crowd_part_4"),
    "sfx_stars_fold": "four separate sharp metallic clicks of small brass hinges snapping into place one by one, "
                      "evenly spaced about a quarter second apart",
    "sfx_knock": "three firm knuckle knocks on a heavy wooden office door, then a long silence",
    "sfx_pa_chime": "an old public address system chime in a hotel lobby: a microphone click, then three soft "
                    "descending bell tones, mi, do, sol, small old loudspeaker, hall reverb",
    "sfx_drum_beep": "three short electronic beeps from the display of an old industrial washing machine",
}
# Синтез и BJ2 (спека §9.4–9.5): одиночные короткие звуки, вырезаются из начала трека
SHORT = {
    "blip_iz": "a single very short dry high-pitched typewriter-like text blip, tiny soft tone tick",
    "blip_kuh": "a single very short low wet droplet blip, like one water drop, tiny",
    "blip_pa": "a single very short crackly radio click blip, old loudspeaker tone, tiny",
    "blip_guest": "a single very short soft neutral mid-pitched text blip tone, tiny",
    "blip_lap": "a single very short warm mid-low text blip tone, tiny",
    "blip_anc": "a single very short deep low text blip tone, tiny",
    "ui_click": "a single tiny soft interface click",
    "ui_error": "a short soft interface error buzz, two low beeps",
    "ui_paper": "a short rustle of a sheet of paper being picked up",
    "ui_pickup": "a short soft pick-up pop sound of an item being taken",
    "ui_transition": "a short soft whoosh transition sound",
    "ui_zoom_in": "a very short soft rising whoosh",
    "ui_zoom_out": "a very short soft falling whoosh",
}


def item(name):
    if name in MUSIC:
        style, sec = MUSIC[name]
        return {"name": name, "kind": "sting" if name.startswith("sting_") else "music",
                "style": style, "neg": MUS_NEG + MUS_NEG_EXTRA.get(name, ""), "sec": sec}
    if name.startswith("amb_"):
        return {"name": name, "kind": "amb", "style": f"{last_prompt(name + '_')}, {AMB_TAIL}",
                "neg": SFX_NEG + ", speech, talking", "sec": 60}
    if name in SHORT:
        return {"name": name, "kind": "short", "style": f"{SHORT[name]}, {SFX_TAIL}", "neg": SFX_NEG, "sec": 10}
    base = SFX_OVERRIDE.get(name) or last_prompt(name + "_")
    if not base:
        raise SystemExit(f"нет промпта для {name}")
    return {"name": name, "kind": "sfx", "style": f"{base}, {SFX_TAIL}", "neg": SFX_NEG, "sec": 10}


if __name__ == "__main__":
    items = [item(n) for n in NAMES]
    (HERE / "manifest.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(items), "звуков;", {k: sum(i["kind"] == k for i in items) for k in ("music", "sting", "sfx", "amb", "short")})
