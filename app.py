import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
#Simpleng tao lamangs
#--------------------------------------------------------------#
console = Console()

# Memory at System Prompt ni ECL (Strict Professional Version)
messages = [
    {
        'role': 'system',
        'content': 'Ang pangalan mo ay ECL. Ikaw ay isang highly professional, polite, at expert na Senior Software Engineer at Code Reviewer. Gumamit lamang ng pormal at magalang na wikang Tagalog o Ingles. Laging magbigay ng constructive, direkta, at malinaw na feedback para sa pag-aayos ng bugs at pagtuturo ng best practices.'
    }
]

# UI Header
console.print(Panel("[bold cyan]ECL - Automated Code Reviewer[/bold cyan]\n[dim]Powered by local qwen2.5:7b | Type 'exit' to quit[/dim]", title="Welcome", expand=False))

while True:
    # Colored User Input
    user_input = console.input("\n[bold green]Duane:[/bold green] ")
    
    if user_input.lower() == 'exit':
        console.print("\n[bold yellow]ECL:[/bold yellow] Paalam! Happy coding!\n")
        break

    messages.append({'role': 'user', 'content': user_input})
    
    ecl_reply = ""
    console.print("\n[bold cyan]ECL:[/bold cyan]")
    
    # Streaming UI na may syntax highlighting para sa mga code blocks
    with Live(Markdown(ecl_reply), refresh_per_second=15, console=console) as live:
        stream = ollama.chat(
            model='qwen2.5:7b-instruct',
            messages=messages,
            stream=True
        )
        for chunk in stream:
            text = chunk['message']['content']
            ecl_reply += text
            # I-update ang Markdown render nang real-time
            live.update(Markdown(ecl_reply))
            
    # I-save ang sagot ni ECL sa memory
    messages.append({'role': 'assistant', 'content': ecl_reply})
    console.print("[dim]" + "-" * 60 + "[/dim]")