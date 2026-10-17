# ECL - Local AI Automated Code Reviewer

An offline, fully local, AI-powered automated code reviewer built with Python, Ollama, and the Rich CLI library. This tool acts as a professional Senior Software Engineer right in your terminal, providing constructive feedback, bug fixes, and best practices across various programming languages.

## The Story Behind ECL

ECL is a special project named after my baby, **Eshien Castillo Laluan**. It serves as a personal inspiration and a showcase of integrating local Large Language Models (LLMs) into practical software development workflows.

## Features

- **Fully Local & Private:** Powered by Ollama (`qwen2.5:7b-instruct`), meaning zero API costs and complete data privacy. Your code never leaves your machine.
- **Polyglot Developer:** Capable of reviewing code in Java, C#, Python, JavaScript, Rust, C++, and more.
- **Professional Feedback:** Strictly prompted to act as a polite and expert Senior Developer.
- **Beautiful Terminal UI:** Utilizes the `rich` Python library for live streaming responses, syntax highlighting, and clean markdown rendering directly in the command line.
- **Contextual Memory:** Remembers the conversation history within the session for seamless debugging.

## Prerequisites

Before running ECL, ensure you have the following installed on your machine:

- [Python 3.8+ or my current Python 3.11.9](https://www.python.org/downloads/)
- [Ollama](https://ollama.com/)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Duanemaster/local-ai-reviewer-ecl.git](https://github.com/Duanemaster/local-ai-reviewer-ecl.git)
   cd local-ai-reviewer-ecl
   ```
