# PDF2Pod: PDF to Podcast Generator

## Introduction

The PDF to Podcast Generator is an innovative tool that transforms academic papers or any PDF document into an engaging podcast-style audio file. This project leverages the power of AI to generate natural-sounding dialogues and convert them into audio, creating an immersive listening experience from written content.

Key features:
- Converts PDF documents into podcast-style audio files
- Utilizes OpenAI's GPT models for dialogue generation
- Uses ElevenLabs' text-to-speech API for realistic voice generation
- Allows user instructions to customize the podcast content

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pdf-to-podcast-generator.git
   cd pdf-to-podcast-generator
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up API keys:
   - Obtain API keys from [OpenAI](https://openai.com/) and [ElevenLabs](https://elevenlabs.io/)
   - Create a `.env` file in the project root and add your API keys:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
     ```

## Usage

1. Run the Gradio app:
   ```
   python app.py
   ```

2. Open the provided URL in your web browser.

3. Upload a PDF file, enter any specific instructions, and provide your API keys.

4. Click "Submit" and wait for the podcast to be generated.

5. Listen to or download the generated podcast audio file.

## Demo

Here is an example of using the PDF to Podcast Generator.



