import os
from dotenv import load_dotenv
import hashlib
import queue
from typing import List, Dict, Any
from pydub import AudioSegment
from tqdm.auto import tqdm
import httpx
import backoff
import asyncio

load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"


def get_clip_filename(speaker: str, text: str, output_dir: str):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return os.path.join(output_dir, f"{speaker}_{text_hash}.wav")


async def generate_voice_clips(dialogue: List[Dict[str, Any]],
                               output_dir: str = "audio_clips"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    dialogue_queue = queue.Queue()
    for line in dialogue:
        dialogue_queue.put(line)
        if "overlaps" in line:
            for overlap in line.get("overlaps"):
                dialogue_queue.put(overlap)

    @backoff.on_exception(backoff.expo,
                          httpx.HTTPStatusError,
                          max_tries=5,
                          giveup=lambda e: e.response.status_code != 429)
    async def generate_audio(line, previous_text=None):
        speaker = line.get("speaker")
        text = line.get("text")
        speaker_voice_id = line.get("speaker_voice_id")
        filename = get_clip_filename(speaker, text, output_dir)
        if os.path.exists(filename):
            return

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
            },
            "output_format": "mp3_44100_128",
            "enable_logging": False,
            "previous_text": previous_text,
            "seed": 42
        }
        try:
            async with httpx.AsyncClient(timeout=600) as client:
                response = await client.post(
                    f"{ELEVEN_LABS_API_URL}/{speaker_voice_id}",
                    headers=headers,
                    json=data)
                response.raise_for_status()
                with open(filename, "wb") as f:
                    f.write(response.content)
        except httpx.HTTPStatusError as e:
            print(f"Failed to generate audio for {speaker}: {e}")

    semaphore = asyncio.Semaphore(2)
    tasks = []
    previous_text = None

    while not dialogue_queue.empty():
        line = dialogue_queue.get()
        await semaphore.acquire()
        task = asyncio.create_task(generate_audio(line, previous_text))
        task.add_done_callback(lambda _: semaphore.release())
        tasks.append(task)
        previous_text = line.get("text")
    for task in tqdm.as_completed(tasks):
        await task


def join_audio_clips(dialogue: List[Dict[str, Any]],
                     output_dir: str = "audio_clips",
                     output_file: str = "final_output_1.wav"):
    output_audio = AudioSegment.silent(duration=0)

    for ix, line in enumerate(
            tqdm(dialogue, desc="Joining audio clips", leave=False)):
        speaker = line.get("speaker")
        text = line.get("text")
        filename = get_clip_filename(speaker, text, output_dir)
        try:
            clip = AudioSegment.from_file(file=filename)
        except FileNotFoundError:
            print(f"Audio clip not found: {filename}")
            continue

        # print(f"Length of clip before adding crossfade: {len(clip)} ms")
        # print(
        #     f"Length of output_audio before adding clip: {len(output_audio)} ms"
        # )

        # print(f"Length of clip before adding crossfade: {len(clip)} ms")
        # print(
        #     f"Length of output_audio before adding clip: {len(output_audio)} ms"
        # )

        if "overlaps" in line:
            # print(f"Line: {line} has overlaps")
            for overlap in line.get("overlaps"):
                overlap_filename = get_clip_filename(overlap.get("speaker"),
                                                     overlap.get('text'),
                                                     output_dir)
                try:
                    print(f"Overlap filename: {overlap_filename}")
                    overlap_clip = AudioSegment.from_file(
                        file=overlap_filename)
                except FileNotFoundError:
                    print(f"Overlap audio clip not found: {overlap_filename}")
                    continue
                overlap_start_time = max(0, len(clip) - 850)
                overlap_start_time = max(0, len(clip) - 850)
                clip = clip.overlay(overlap_clip, position=overlap_start_time)
                if len(overlap_clip) > 850:
                    remaining_overlap = overlap_clip[850:]
                    clip = clip.append(remaining_overlap, crossfade=0)
        if len(clip) < 10 or len(output_audio) < 10:
            crossfade_duration = 0
        else:
            crossfade_duration = min(10,
                                     len(clip) // 2,
                                     len(output_audio) // 2)
        print(f"Crossfade duration: {crossfade_duration} ms")
        output_audio = output_audio.append(clip, crossfade=crossfade_duration)

    output_audio.export(output_file, format="wav")


# Example usage
if __name__ == "__main__":
    import asyncio
    input_dialogue = [{
        "speaker": "Jessica",
        "text":
        "Welcome, everyone, to today's discussion. We're diving into MemGPT and its innovative approach to memory management in large language models.",
        "speaker_voice_id": "fNmfW5GlQ7PDakGkiTzs"
    }, {
        "speaker":
        "Michael",
        "text":
        "Thanks, Jessica! I've always found the concept of limitations in LLMs quite fascinating. But how exactly does MemGPT tackle these constraints?",
        "speaker_voice_id":
        "iP95p4xoKVk53GoZ742B",
        "overlaps": [{
            "speaker": "Emily",
            "text":
            "Oh, I was wondering the same thing! Especially in terms of document analysis and conversations.",
            "speaker_voice_id": "cgSgspJ2msm6clMCkdW9"
        }]
    }, {
        "speaker":
        "David",
        "text":
        "Essentially, MemGPT uses a method akin to virtual memory in computers. It handles hierarchical memory management, mimicking how an OS would deal with overflow by paging. This way, the system can seemingly manage more data than its context window allows.",
        "speaker_voice_id":
        "cjVigY5qzO86Huf0OWal",
        "overlaps": [{
            "speaker": "Jessica",
            "text":
            "That's interesting\u2014it sounds like a computer handling its RAM efficiently.",
            "speaker_voice_id": "fNmfW5GlQ7PDakGkiTzs"
        }]
    }, {
        "speaker": "Emily",
        "text":
        "So, it's like increasing the room size without actually adding more room? By using data movement techniques similar to those in a computer's memory system?",
        "speaker_voice_id": "cgSgspJ2msm6clMCkdW9"
    }, {
        "speaker": "Michael",
        "text":
        "Exactly. And what's brilliant is MemGPT's ability to do this autonomously through function calls\u2014kind of like it has the keys to its own memory bank.",
        "speaker_voice_id": "iP95p4xoKVk53GoZ742B"
    }, {
        "speaker": "Jessica",
        "text":
        "So, we're talking about independence from human intervention, which is pivotal in applications like virtual assistants, right?",
        "speaker_voice_id": "fNmfW5GlQ7PDakGkiTzs"
    }, {
        "speaker": "David",
        "text":
        "Precisely, Jessica. This autonomy translates into better efficiency and user experience, where MemGPT personalizes and evolves based on extended interactions.",
        "speaker_voice_id": "cjVigY5qzO86Huf0OWal"
    }, {
        "speaker": "Emily",
        "text":
        "I can imagine how this would significantly enhance interaction in conversational agents. But what about document analysis\u2014how does MemGPT improve there?",
        "speaker_voice_id": "cgSgspJ2msm6clMCkdW9"
    }, {
        "speaker": "David",
        "text":
        "In document analysis, MemGPT gives the system the capacity to handle documents that exceed the typical context window, paging information in and out at need. It's like a librarian fetching a book based on what you're asking for.",
        "speaker_voice_id": "cjVigY5qzO86Huf0OWal"
    }, {
        "speaker": "Michael",
        "text":
        "With this design, MemGPT effectively expands the usable memory without the exponentially higher costs associated with longer context models.",
        "speaker_voice_id": "iP95p4xoKVk53GoZ742B"
    }, {
        "speaker": "Jessica",
        "text":
        "Wrapping it up, MemGPT seems to offer a bridge over the limitations of traditional LLMs, allowing for more complex, engaging, and extended usage in AI applications. Any last thoughts?",
        "speaker_voice_id": "fNmfW5GlQ7PDakGkiTzs"
    }, {
        "speaker": "Emily",
        "text":
        "I think it's a game-changer for AI in handling extensive and dynamic content.",
        "speaker_voice_id": "cgSgspJ2msm6clMCkdW9"
    }, {
        "speaker": "David",
        "text":
        "Absolutely. MemGPT has the potential to redefine how we approach LLM constraints\u2014we're definitely looking at a promising future for AI-powered solutions.",
        "speaker_voice_id": "cjVigY5qzO86Huf0OWal"
    }]

    # Generate voice clips
    asyncio.run(generate_voice_clips(input_dialogue, "audio_clips_1"))

    # Join audio clips with overlaps
    join_audio_clips(input_dialogue, "audio_clips_1",
                     "full_podcast_overlay_1500secs.wav")
