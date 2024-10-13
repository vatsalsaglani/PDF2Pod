import os
import gradio as gr
from podcast import generate_podcast
from uuid import uuid4


async def process_pdf(pdf_file, user_instruction):
    pdf_path = pdf_file.name
    uuid = str(uuid4())
    output_dir = f"output_{uuid}"
    os.makedirs(output_dir, exist_ok=True)

    await generate_podcast(pdf_path, output_dir, user_instruction)

    output_file = os.path.join(output_dir, "full_podcast.wav")
    return output_file


iface = gr.Interface(
    fn=process_pdf,
    inputs=[
        gr.File(label="Upload PDF", file_types=[".pdf"]),
        gr.Textbox(label="User Instructions",
                   placeholder=
                   "Enter specific areas or instructions for the podcast...")
    ],
    outputs=gr.Audio(label="Generated Podcast"),
    title="PDF2Pod: PDF to Podcast Generator",
    description=
    "Upload a PDF file and provide instructions to generate a podcast-style audio file.",
)

if __name__ == "__main__":
    iface.launch()
