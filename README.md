# o1 Auto Teacher 🎓

An interactive AI-powered learning experience generator that creates comprehensive, multimedia educational content on any topic.

## Features ✨

- **Dynamic Content Generation**: Uses AI to create structured, easy-to-understand chapters about any topic
- **Rich Multimedia Experience**:
  - 🎨 AI-generated images for visual learning
  - 🎧 Text-to-speech narration for auditory learning
  - 📱 Responsive web interface with dark mode
  - ✨ Smooth animations and transitions

## 🎥 Watch How It's Built!

**[Watch the complete build process on Patreon](https://www.patreon.com/posts/how-to-build-o1-112197565?utm_medium=clipboard_copy&utm_source=copyLink&utm_campaign=postshare_creator&utm_content=join_link)**

Dive deep into the development process with:

- 🎯 Step-by-step video walkthrough of the entire build
- 💡 Expert insights and best practices

Plus, get access to my exclusive **30-Chapter Cursor Mastery Course**:

- 📚 20+ hours of hands-on content
- 🛠️ Build full applications from scratch in each chapter
- ⚡ Quick, independent chapters for rapid learning
- 🎓 From basics to advanced Cursor techniques

## ❤️ Support & Get 400+ AI Projects

This is one of 400+ fascinating projects in my collection! [Support me on Patreon](https://www.patreon.com/c/echohive42/membership) to get:

- 🎯 Access to 400+ AI projects (and growing daily!)
  - Including advanced projects like [2 Agent Real-time voice template with turn taking](https://www.patreon.com/posts/2-agent-real-you-118330397)
- 📥 Full source code & detailed explanations
- 📚 1000x Cursor Course
- 🎓 Live coding sessions & AMAs
- 💬 1-on-1 consultations (higher tiers)
- 🎁 Exclusive discounts on AI tools & platforms (up to $180 value)

## Prerequisites 📋

- Python 3.7+
- OpenAI API key (set as system environment variable)

## Installation 🚀

1. Clone the repository:
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key as a system environment variable:

```bash
# For Windows
set OPENAI_API_KEY=your-api-key-here

# For Unix/Linux/MacOS
export OPENAI_API_KEY=your-api-key-here
```

## Usage 💡

1. Run the script:

```bash
python auto_teacher.py
```

2. Enter any topic you want to learn about when prompted
3. Wait while the AI generates your personalized learning experience:
   - Creates structured chapters
   - Generates relevant images
   - Converts text to speech
   - Builds an interactive HTML interface
4. Open the generated HTML file in your browser (located in `topics/[your-topic]/index.html`)

## Project Structure 📁

```
auto_teacher/
├── topics/                 # Generated content directory
│   └── [topic-name]/      # Topic-specific directory
│       ├── index.html     # Interactive learning interface
│       └── static/        # Static assets directory
│           ├── images/    # Generated images
│           └── audio/     # Generated audio files
└── auto_teacher.py        # Main script
```

## Technical Details 🔧

- **AI Models Used**:

  - Text Generation: o1-mini
  - Image Generation: DALL-E 3
  - Text-to-Speech: TTS-1
- **Frontend Technologies**:

  - DaisyUI for UI components
  - Tailwind CSS for styling
  - Anime.js for animations
  - Vanilla JavaScript for interactivity

## Features in Detail 🎯

1. **Content Generation**

   - AI-generated chapters with titles and descriptions
   - Each chapter includes custom image descriptions
2. **Interactive UI**

   - Dark mode interface
   - Play all chapters sequentially
   - Individual chapter playback control
   - Smooth scrolling and animations
   - Responsive design for all devices
3. **Error Handling**

   - Comprehensive error catching and reporting
   - Informative colored console output
   - Graceful failure handling

## Contributing 🤝

Feel free to submit issues and enhancement requests!

## License 📄

[Your chosen license]

## Acknowledgments 🙏

- OpenAI for AI models
- DaisyUI for UI components
- Anime.js for animations
