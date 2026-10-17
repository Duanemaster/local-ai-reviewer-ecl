# ECL - Local AI Automated Code Reviewer

An offline, fully local, AI-powered automated code reviewer desktop application built with Python, CustomTkinter, and Ollama. This tool acts as a professional Senior Software Engineer right on your desktop, providing constructive feedback, bug fixes, and best practices across various programming languages.

## The Story Behind ECL

ECL is a special project named after my baby, **Eshien Castillo Laluan**. It serves as a personal inspiration and a showcase of integrating local Large Language Models (LLMs) into practical software development workflows.

## Disclaimer: Still Improving

**Status: Work in Progress.**
ECL is currently under active development. You may encounter occasional UI bugs, model hallucinations on highly complex codebases, or formatting glitches. Further optimizations (like syntax highlighting and multi-file analysis) are actively being developed.

## Features

- **Fully Local & Private:** Powered by Ollama (`qwen2.5:7b-instruct`), meaning zero API costs and complete data privacy. Your code never leaves your machine.
- **Modern Desktop GUI:** Built with `customtkinter` featuring a Split Layout (Code Editor on the left, Review Feedback on the right) instead of a basic terminal interface.
- **Thread-Safe & Responsive:** Asynchronous background processing ensures the UI never freezes during heavy code analysis.
- **Anti-Hallucination Measures:** Strict system prompting and a large context window (`num_ctx=8192`) force the model to cite line numbers and avoid inventing errors.
- **File Management:** Directly open `.py`, `.cs`, `.java`, `.js`, etc., and export the AI's review as a Markdown (`.md`) report.
- **Severity Labeling:** Findings are automatically categorized into Bug, Warning, or Suggestion.

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
