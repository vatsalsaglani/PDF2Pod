import json
from llm import OpenAIWrapper
from prompts import DIALOGUE_PROMPT
from pdf_reader import parse_pdf
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

openai_wrapper = OpenAIWrapper()


class Scratchpad(BaseModel):
    observation: str = Field(
        ..., description="An observation from the input document.")
    idea: str = Field(..., description="A brainstorming idea for the dialogue")
    outline: str = Field(...,
                         description="A rough outline based on the dialogue")
    key_insights: str = Field(
        ..., description="The key takeaways from the idea and the outline")


class Speaker(BaseModel):
    speaker_name: str
    speaker_voice_id: Literal[
        "fNmfW5GlQ7PDakGkiTzs", "iP95p4xoKVk53GoZ742B", "cjVigY5qzO86Huf0OWal",
        "cgSgspJ2msm6clMCkdW9", "vipJZKBNu38Qo9xBYnTn", "qPhq8YzcFyamA1iXeyEU",
        "qPhq8YzcFyamA1iXeyEU"]  # aaradhya (female), chris (male), eric (male), jessica (female), ramkrishnan (male), sally (female), sundara (female)


class ScratchpadIdeas(BaseModel):
    about_the_document: str = Field(
        ...,
        description=
        "A summary of the document in a few sentences. This is used to understand the document better."
    )
    ideas: List[Scratchpad] = Field(
        ...,
        description=
        "A list of brainstorming ideas for the dialogue starting with observation",
        # min_length=10
    )
    speakers: List[Speaker] = Field(
        ..., description="The list of speakers in the dialogue")


class Overlap(BaseModel):
    speaker: str = Field(..., description="The speaker of the dialogue turn")
    text: str = Field(...,
                      max_length=400,
                      description="The text of the dialogue turn")
    speaker_voice_id: str = Field(
        ..., description="The voice id of the speaker of the dialogue turn")


class DialogueTurn(BaseModel):
    speaker: str = Field(..., description="The speaker of the dialogue turn")
    text: str = Field(..., description="The text of the dialogue turn")
    speaker_voice_id: str = Field(
        ..., description="The voice id of the speaker of the dialogue turn")
    overlaps: Optional[List[Overlap]] = Field(
        default=None,
        description=
        "The list of dialogue turns that overlap with this dialogue turn")


class Dialogue(BaseModel):
    dialogue: List[DialogueTurn] = Field(
        ...,
        description="The dialogue turns in the dialogue",
        # min_length=20
    )


print(DialogueTurn.model_json_schema())


async def generate_scratchpad_ideas(text: str, **kwargs) -> ScratchpadIdeas:
    """
    Generate a list of brainstorming ideas for the dialogue from the given text using the OpenAI API.
    """
    functions = [{
        "name": "generate_scratchpad_ideas",
        "description":
        "Generate a list of brainstorming ideas for the dialogue from the given text",
        "parameters": ScratchpadIdeas.model_json_schema()
    }]
    messages = [{"role": "system", "content": DIALOGUE_PROMPT}]
    user_msg = f"<input_text>\n{text}\n</input_text>\nGenerate scratchpad ideas based on the above text."
    if "user_instruction" in kwargs:
        user_msg += f"\n<user_instruction>\n{kwargs['user_instruction']}\n</user_instruction>"
    messages.append({"role": "user", "content": user_msg})
    response = await openai_wrapper.function_call("gpt-4o",
                                                  messages,
                                                  functions,
                                                  max_tokens=4096)
    return json.loads(response.arguments)


async def generate_dialogue(text: str, user_instruction: str = ""):
    """
    Generate a dialogue from the given text using the OpenAI API.
    """
    scratchpad_ideas = await generate_scratchpad_ideas(
        text, user_instruction=user_instruction)
    print("Scratchpad Ideas: \n", json.dumps(scratchpad_ideas, indent=2))
    messages = [{
        "role": "system",
        "content": DIALOGUE_PROMPT
    }, {
        "role":
        "user",
        "content":
        f"Input Text: <input_text>\n{text}</input_text>\n\nFollowing are the scratchpad ideas\n<scratchpad>\n{scratchpad_ideas}\n</scratchpad>\n\nUser Instruction: <user_instruction>\n{user_instruction}\n</user_instruction>"
    }]
    functions = [{
        "name": "generate_dialogue",
        "description":
        "Generate a dialogue from the given text using the OpenAI API.",
        "parameters": Dialogue.model_json_schema()
    }]
    response = await openai_wrapper.function_call(
        "gpt-4o",
        messages,
        functions,
        function_call="generate_dialogue",
        max_tokens=8192)
    return json.loads(response.arguments)


if __name__ == "__main__":
    import asyncio
    text = parse_pdf("/Users/vatsalsaglani/Downloads/papers/2310.08560.pdf")
    text = list(
        filter(lambda t: [t for t in t if t["type"] == "text"],
               list(map(lambda x: x["content"], text))))

    flatten = [item for sublist in text for item in sublist]
    # print(flatten)
    flattent = list(
        map(lambda x: x["text"],
            list(filter(lambda t: t["type"] == "text", flatten))))
    text = "\n".join(flattent)
    # print(f"TEXT: ", json.dumps(text, indent=2))
    print(json.dumps(asyncio.run(generate_dialogue(text)), indent=2))
