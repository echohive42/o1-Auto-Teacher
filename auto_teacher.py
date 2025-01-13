import json
import os
from openai import AsyncOpenAI
from termcolor import colored
import base64
import asyncio
import aiohttp
import aiofiles
import re

# Constants
OPENAI_TEXT_MODEL = "o1-mini"
OPENAI_IMAGE_MODEL = "dall-e-3"
OPENAI_TTS_MODEL = "tts-1"
MAX_TOPIC_LENGTH = 50

def sanitize_topic(topic):
    """Sanitize topic name for file system use"""
    # Remove special characters and replace spaces with underscores
    sanitized = re.sub(r'[^\w\s-]', '', topic)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    # Truncate to max length
    return sanitized[:MAX_TOPIC_LENGTH].lower().strip('_')

def ensure_topic_directory(topic):
    """Create directory structure for the topic"""
    sanitized_topic = sanitize_topic(topic)
    topic_dir = os.path.join("topics", sanitized_topic)
    static_dir = os.path.join(topic_dir, "static")
    
    # Create main directories
    os.makedirs(topic_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
    
    return {
        "topic_dir": topic_dir,
        "static_dir": static_dir,
        "html_file": os.path.join(topic_dir, "index.html")
    }

client = AsyncOpenAI()

async def parse_xml_content(text):
    """Parse XML-like tags from text for mini/preview models"""
    try:
        chapters = []
        import re
        
        # Find all chapter blocks
        chapter_blocks = re.findall(r'<chapter>(.*?)</chapter>', text, re.DOTALL)
        
        for block in chapter_blocks:
            # Extract individual fields
            title = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
            desc = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
            img_desc = re.search(r'<image_description>(.*?)</image_description>', block, re.DOTALL)
            
            if title and desc and img_desc:
                chapters.append({
                    "title": title.group(1).strip(),
                    "description": desc.group(1).strip(),
                    "image_description": img_desc.group(1).strip()
                })
        
        return {"chapters": chapters}
    except Exception as e:
        print(colored(f"Error parsing XML content: {str(e)}", "red"))
        raise

async def generate_content(topic):
    try:
        print(colored("Generating educational content...", "cyan"))
        
        # Check if using mini/preview model
        is_mini_model = "-" in OPENAI_TEXT_MODEL
        
        if is_mini_model:
            # For mini/preview models, use XML-like structure
            prompt = f"""
            Please explain {topic} in a way that is comprehensive and easy to understand.
            Return the response in the following XML-like format:
            
            <chapter>
            <title>Title of the chapter</title>
            <description>short content for the chapter</description>
            <image_description>Fun and informative image description for DALL-E</image_description>
            </chapter>
            
            Create multiple chapters using this format. Each chapter should cover a different aspect of the topic.
            Make sure to properly close all tags and use clear, descriptive titles.
            """
            
            messages = [{"role": "user", "content": prompt}]
            response_format = None  # No JSON format for mini models
            
        else:
            # For o1 model, use JSON format
            system_message = """Please explain the user given topic in a way that is comprehensive and easy to understand.
            Also return image descriptions for each chapter (fun and informative description - will be used with a text to image model).
Please return the response in a json format with the following keys:
            {
                "chapters": [
{
    "title": "title of the chapter",
    "description": "short content for the chapter",
    "image_description": "image description of the chapter"
}
                ]
            }
            """
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"please explain {topic}"}
            ]
            response_format = {"type": "json_object"}
        
        response = await client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=messages,
            response_format=response_format
        )
        
        content = response.choices[0].message.content
        
        if is_mini_model:
            # Parse XML-like structure for mini models
            return await parse_xml_content(content)
        else:
            # Parse JSON for o1 model
            return json.loads(content)
            
    except Exception as e:
        print(colored(f"Error generating content: {str(e)}", "red"))
        raise

async def generate_image(image_description, index):
    try:
        print(colored(f"Generating image for chapter {index + 1}...", "cyan"))
        response = await client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=image_description,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        print(colored(f"Error generating image: {str(e)}", "red"))
        raise

async def generate_speech(text, index, static_dir):
    try:
        print(colored(f"Generating speech for chapter {index + 1}...", "cyan"))
        speech_file_path = os.path.join(static_dir, "audio", f"chapter_{index}.mp3")
        
        response = await client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice="alloy",
            input=text
        )
        
        async with aiofiles.open(speech_file_path, 'wb') as f:
            await f.write(response.read())
            
        return f"static/audio/chapter_{index}.mp3"
    except Exception as e:
        print(colored(f"Error generating speech: {str(e)}", "red"))
        raise

async def download_image(image_url, index, static_dir):
    try:
        print(colored(f"Downloading image for chapter {index + 1}...", "cyan"))
        image_filename = f"chapter_{index}.png"
        image_path = os.path.join(static_dir, "images", image_filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    async with aiofiles.open(image_path, 'wb') as f:
                        await f.write(image_data)
                    return f"static/images/{image_filename}"
                else:
                    raise Exception(f"Failed to download image: {response.status}")
    except Exception as e:
        print(colored(f"Error downloading image: {str(e)}", "red"))
        raise

async def process_chapter(chapter, index):
    """Process a single chapter's image and audio in parallel"""
    try:
        # Get image URL from DALL-E
        image_url = await generate_image(chapter["image_description"], index)
        # Download image and get audio in parallel
        image_task = download_image(image_url, index)
        speech_task = generate_speech(chapter["description"], index)
        
        # Wait for both tasks to complete
        local_image_path, audio_path = await asyncio.gather(image_task, speech_task)
        
        return {
            "image_url": local_image_path,
            "audio_url": audio_path
        }
    except Exception as e:
        print(colored(f"Error processing chapter {index + 1}: {str(e)}", "red"))
        raise

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Learning Experience</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.4/dist/full.css" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
    <style>
        .chapter-container {
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
        }
        .chapter-container.playing {
            background-color: rgba(59, 130, 246, 0.1); /* Light blue background */
            border-left: 4px solid #3b82f6; /* Blue accent border */
            transform: scale(1.01);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        .loading-animation {
            width: 50px;
            height: 50px;
            border: 5px solid #ddd;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        audio {
            width: 100%;
            margin-top: 1rem;
            border-radius: 0.5rem;
            background-color: #2a303c;
        }
        audio::-webkit-media-controls-panel {
            background-color: #2a303c;
        }
        .chapter-image {
            width: 100%;
            height: 400px;
            object-fit: cover;
            border-radius: 1rem;
            margin: 1rem 0;
        }
    </style>
</head>
<body class="min-h-screen bg-base-300">
    <div class="container mx-auto px-4 py-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-4" id="mainTitle">Interactive Learning Experience</h1>
            <button id="playAll" class="btn btn-primary btn-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Play All
            </button>
        </div>

        <div id="chapters" class="space-y-8">
            <!-- Chapters will be inserted here -->
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            anime({
                targets: '.chapter-container',
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(200),
                easing: 'easeOutExpo'
            });

            const audioElements = document.querySelectorAll('audio');
            let currentlyPlaying = null;
            let currentlyPlayingContainer = null;

            function scrollToElement(element) {
                const offset = 100;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }

            function highlightChapter(chapterElement) {
                // Remove highlight from previous chapter
                if (currentlyPlayingContainer) {
                    currentlyPlayingContainer.classList.remove('playing');
                }
                // Add highlight to current chapter
                chapterElement.classList.add('playing');
                currentlyPlayingContainer = chapterElement;
            }

            audioElements.forEach(audio => {
                const chapterContainer = audio.closest('.chapter-container');
                
                audio.addEventListener('play', () => {
                    if (currentlyPlaying && currentlyPlaying !== audio) {
                        currentlyPlaying.pause();
                    }
                    currentlyPlaying = audio;
                    scrollToElement(chapterContainer);
                    highlightChapter(chapterContainer);
                });

                audio.addEventListener('ended', () => {
                    chapterContainer.classList.remove('playing');
                    if (currentlyPlayingContainer === chapterContainer) {
                        currentlyPlayingContainer = null;
                    }
                });

                audio.addEventListener('pause', () => {
                    if (!audio.ended) {
                        chapterContainer.classList.remove('playing');
                        if (currentlyPlayingContainer === chapterContainer) {
                            currentlyPlayingContainer = null;
                        }
                    }
                });
            });

            const playAllButton = document.getElementById('playAll');
            let currentAudioIndex = 0;

            playAllButton.addEventListener('click', () => {
                if (currentlyPlaying) {
                    currentlyPlaying.pause();
                }
                playAllButton.disabled = true;
                currentAudioIndex = 0;
                playAudioSequentially();
            });

            function playAudioSequentially() {
                if (currentAudioIndex < audioElements.length) {
                    const audio = audioElements[currentAudioIndex];
                    const chapterContainer = audio.closest('.chapter-container');
                    
                    if (currentlyPlaying && currentlyPlaying !== audio) {
                        currentlyPlaying.pause();
                    }
                    currentlyPlaying = audio;
                    
                    scrollToElement(chapterContainer);
                    highlightChapter(chapterContainer);
                    
                    audio.play();

                    audio.addEventListener('ended', () => {
                        currentAudioIndex++;
                        playAudioSequentially();
                    }, { once: true });
                } else {
                    currentAudioIndex = 0;
                    currentlyPlaying = null;
                    if (currentlyPlayingContainer) {
                        currentlyPlayingContainer.classList.remove('playing');
                        currentlyPlayingContainer = null;
                    }
                    playAllButton.disabled = false;
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            }
        });
    </script>
</body>
</html>
"""

async def generate_html(content, topic, html_file):
    try:
        chapters_html = ""
        for chapter in content["chapters"]:
            chapters_html += f"""
                <div class="chapter-container card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <h2 class="card-title text-2xl">{chapter['title']}</h2>
                        <img src="{chapter['image_url']}" alt="{chapter['title']}" class="w-full h-64 object-cover rounded-xl">
                        <p class="text-lg">{chapter['description']}</p>
                        <div class="card-actions justify-end">
                            <audio controls class="w-full">
                                <source src="{chapter['audio_url']}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                    </div>
                </div>
            """
        
        html_content = HTML_TEMPLATE.replace(
            "<!-- Chapters will be inserted here -->", 
            chapters_html
        ).replace(
            "Interactive Learning Experience",
            f"Learning About {topic.title()}"
        )
        
        async with aiofiles.open(html_file, 'w', encoding="utf-8") as f:
            await f.write(html_content)
            
        print(colored(f"HTML file generated: {html_file}", "green"))
    except Exception as e:
        print(colored(f"Error generating HTML: {str(e)}", "red"))
        raise

async def create_learning_experience(topic):
    try:
        # Create directory structure
        dirs = ensure_topic_directory(topic)
        
        # Generate content first
        content = await generate_content(topic)
        
        # Create all tasks in parallel
        all_tasks = []
        
        print(colored("Generating all content in parallel...", "cyan"))
        
        # Start all image and speech generation tasks immediately
        for i, chapter in enumerate(content["chapters"]):
            image_task = generate_image(chapter["image_description"], i)
            speech_task = generate_speech(chapter["description"], i, dirs["static_dir"])
            all_tasks.extend([
                {
                    "type": "image",
                    "index": i,
                    "task": image_task
                },
                {
                    "type": "audio",
                    "index": i,
                    "task": speech_task
                }
            ])
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*(task["task"] for task in all_tasks))
        
        # Process results and create download tasks for images
        download_tasks = []
        audio_results = {}
        
        for task, result in zip(all_tasks, results):
            if task["type"] == "image":
                download_tasks.append({
                    "index": task["index"],
                    "task": download_image(result, task["index"], dirs["static_dir"])
                })
            else:
                audio_results[task["index"]] = result
        
        downloaded_images = await asyncio.gather(*(task["task"] for task in download_tasks))
        
        image_paths = {}
        for task, path in zip(download_tasks, downloaded_images):
            image_paths[task["index"]] = path
        
        for i, chapter in enumerate(content["chapters"]):
            chapter.update({
                "image_url": image_paths[i],
                "audio_url": audio_results[i]
            })
        
        # Generate HTML
        await generate_html(content, topic, dirs["html_file"])
        
        print(colored("\n=== Learning Experience Created! ===", "green", attrs=["bold"]))
        print(colored("\nTo view your learning experience:", "yellow"))
        print(colored(f"Open this file in your browser: {os.path.abspath(dirs['html_file'])}", "yellow"))
        print(colored("\nEnjoy learning!", "green"))
        return content
    except Exception as e:
        print(colored(f"Error creating learning experience: {str(e)}", "red"))
        raise

if __name__ == "__main__":
    # Create topics directory if it doesn't exist
    os.makedirs("topics", exist_ok=True)
    
    topic = input(colored("Enter the topic you want to learn about: ", "yellow"))
    asyncio.run(create_learning_experience(topic))
