import os
import json
from dialogue import generate_dialogue
from pdf_reader import parse_pdf
from typing import List, Dict, Union
from voiceover import generate_voice_clips, join_audio_clips


def parse_pdf_to_text(pdf_path: str):
    text = parse_pdf(pdf_path)
    text = list(
        filter(lambda t: [t for t in t if t["type"] == "text"],
               list(map(lambda x: x["content"], text))))

    flatten = [item for sublist in text for item in sublist]
    flattent = list(
        map(lambda x: x["text"],
            list(filter(lambda t: t["type"] == "text", flatten))))
    return "\n".join(flattent)


def add_dialogue_ids(dialogue: List[Dict]):
    ids = 0
    dialogue = dialogue.get("dialogue")
    speakers = set()
    print(f"TYPE: {type(dialogue)}")
    print(json.dumps(dialogue, indent=2))
    for ix, speaker in enumerate(dialogue):
        # dialogue[ix]["id"] = ids
        speakers.add(speaker["speaker"])
        ids += 1
        if "overlaps" in speaker:
            for ixo, overlap in enumerate(speaker["overlaps"]):
                # dialogue[ix]["overlap"][ixo]["id"] = ids
                ids += 1
                speakers.add(overlap["speaker"])
    print(f"TOTAL CLIPS: {ids}")
    return dialogue, speakers


async def generate_podcast(pdf_path: str,
                           path: str = "audio_clips_1",
                           user_instruction: str = ""):
    text = parse_pdf_to_text(pdf_path)
    print(f"TEXT: {text}")
    dialogue = await generate_dialogue(text, user_instruction)
    dialogue, speakers = add_dialogue_ids(dialogue)
    speakers = list(speakers)
    print(f"SPEAKERS: {json.dumps(speakers)}")
    print(f"DIALOGUE: \n{json.dumps(dialogue, indent=2)}")
    await generate_voice_clips(dialogue, path)
    join_audio_clips(dialogue, path, os.path.join(path, "full_podcast.wav"))
