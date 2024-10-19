import os
import logging

from pathlib import Path

import openai

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

def prepare_prompt(articles):
    prompt = """Please provide a concise summary of the following news articles from the last couple of days in a form 
    of one meaningful story about what happened. This summary and you answer should be in fully in Russian. The articles are following: """
    for article in articles:
        prompt += f"**Title:** {article.title}\n**Text:** {article.text}\n\n"
    prompt += "### Summary:"
    return prompt

def get_summary(prompt, max_tokens=5000):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()
        logging.info("successfully retrieved summary")
        return summary
    except Exception as e:
        logging.error(f"error while communicating with OpenAI API: {e}")
        return None

def get_voice(prompt):
    speech_file_path = Path(__file__).parent / "speech" / "speech.mp3"
    response = openai.audio.speech.create(
        model='tts-1',
        voice='nova',
        input=prompt,
    )
    response.write_to_file(speech_file_path)