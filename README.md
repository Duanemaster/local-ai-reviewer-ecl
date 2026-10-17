# ECL - Local AI Automated Code Reviewer

An offline, fully local, AI-powered automated code reviewer desktop application built with Python, CustomTkinter, and Ollama. This tool acts as a professional Senior Software Engineer right on your desktop, providing constructive feedback, bug fixes, and best practices across various programming languages.

## The Story Behind ECL

ECL is a special project named after my baby, **Eshien Castillo Laluan**. It serves as a personal inspiration and a showcase of integrating local Large Language Models (LLMs) into practical software development workflows.

## Disclaimer: Still Improving

**Status: Work in Progress.**
ECL is currently under active development. You may encounter occasional UI bugs, model hallucinations on highly complex codebases, or formatting glitches. Further optimizations (like syntax highlighting and multi-file analysis) are actively being developed.

## Features

- **Fully Local & Private:** Powered by Ollama (default: `qwen2.5:7b-instruct`), meaning zero API costs and complete data privacy. Your code never leaves your machine.
- **Dynamic Model Selection:** Automatically detects and lists all locally installed Ollama models in a dropdown menu for easy switching.
- **Modern Desktop GUI:** Built with `customtkinter` featuring a Split Layout (Code Editor with line numbers on the left, Review Feedback on the right).
- **Custom Dark Dialogs:** Features custom-built dark themed alert and confirmation dialogs for a seamless, immersive UI experience without the glaring white native Tkinter popups.
- **Thread-Safe & Responsive:** Asynchronous background processing ensures the UI never freezes during heavy code analysis.
- **Anti-Hallucination Measures:** Strict system prompting and a large context window (`num_ctx=8192`) force the model to cite line numbers and avoid inventing errors.
- **File Management:** Directly open `.py`, `.cs`, `.java`, `.js`, etc., and export the AI's review as a Markdown (`.md`) report.
- **Modular Architecture:** Cleanly separated codebase (`ecl/` package) handling UI components, AI logic, and application state independently.
- **Standalone Executable:** Includes a build script (`build.bat`) to easily compile the application into a portable `.exe` file using PyInstaller.

## Prerequisites

Before running ECL, ensure you have the following installed on your machine:

- [Python 3.11.9](https://www.python.org/downloads/) (or Python 3.8+)
- [Ollama](https://ollama.com/)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Duanemaster/local-ai-reviewer-ecl.git](https://github.com/Duanemaster/local-ai-reviewer-ecl.git)
   cd local-ai-reviewer-ecl
   ```
