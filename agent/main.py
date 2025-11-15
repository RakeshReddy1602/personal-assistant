import asyncio
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown

from agent.schema.init_assistant_graph import build_graph
from agent.states.assistant_state import AssistantState
from agent.agents.master import push_history


class PersonalAssistantApp(App):
    """A Textual app for Personal Assistant."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #chat-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }
    
    #input-container {
        height: auto;
        padding: 1;
        background: $surface;
    }
    
    #status-bar {
        height: 3;
        padding: 1;
        background: $boost;
        color: $text;
    }
    
    Input {
        border: solid $accent;
    }
    
    RichLog {
        background: $panel;
        border: none;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear", "Clear History"),
        Binding("ctrl+h", "show_history", "Show History"),
    ]
    
    def __init__(self):
        super().__init__()
        load_dotenv()
        
        # Initialize graph and state
        self.graph = build_graph()
        self.state: AssistantState = {
            "category_to_be_served": "",
            "query_to_be_served": "",
            "history": [],
            "response": "",
        }
        self.processing = False
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(id="status-bar"):
            yield Static(
                "🤖 Personal Assistant | Commands: /clear, /history, /state, /help | Ctrl+C: Quit, Ctrl+L: Clear",
                id="status-text"
            )
        
        with Vertical():
            yield RichLog(
                highlight=True,
                markup=True,
                wrap=True,
                id="chat-container"
            )
            
            with Container(id="input-container"):
                yield Input(
                    placeholder="Type your message here... (or /help for commands)",
                    id="user-input"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        chat = self.query_one("#chat-container", RichLog)
        chat.write(Panel(
            "[bold cyan]🤖 Personal Assistant Ready![/bold cyan]\n\n"
            "[yellow]Available Tools:[/yellow] Mail, Calendar, Expense Tracker\n\n"
            "[dim]Commands:[/dim]\n"
            "  • [cyan]/clear[/cyan] - Clear conversation history\n"
            "  • [cyan]/history[/cyan] - Show conversation history\n"
            "  • [cyan]/state[/cyan] - Show current state\n"
            "  • [cyan]/help[/cyan] - Show this help message\n"
            "  • [cyan]Ctrl+C[/cyan] - Quit application",
            title="Welcome",
            border_style="green"
        ))
        
        # Focus the input
        self.query_one("#user-input", Input).focus()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        input_widget = self.query_one("#user-input", Input)
        chat = self.query_one("#chat-container", RichLog)
        
        # Clear input
        input_widget.value = ""
        
        if not user_input:
            return
        
        # Check if already processing
        if self.processing:
            chat.write(Text("⏳ Please wait, still processing previous request...", style="yellow"))
            return
        
        # Handle commands
        if user_input.startswith("/"):
            await self.handle_command(user_input, chat)
            return
        
        # Display user message
        chat.write(Panel(
            Text(user_input, style="bold white"),
            title="[bold green]👤 You[/bold green]",
            border_style="green"
        ))
        
        # Process the query
        await self.process_query(user_input, chat)
    
    async def handle_command(self, command: str, chat: RichLog) -> None:
        """Handle special commands."""
        cmd = command.lower()
        
        if cmd == "/clear":
            self.state["history"] = []
            self.state["query_to_be_served"] = ""
            self.state["category_to_be_served"] = ""
            self.state["response"] = ""
            chat.clear()
            chat.write(Panel(
                "[bold green]✅ History cleared successfully![/bold green]",
                border_style="green"
            ))
        
        elif cmd == "/history":
            history = self.state.get("history", [])
            if not history:
                chat.write(Panel(
                    "[yellow]No conversation history yet.[/yellow]",
                    title="History",
                    border_style="yellow"
                ))
            else:
                history_text = ""
                for i, m in enumerate(history[-10:], 1):  # Show last 10
                    role = m.get('role', 'user')
                    content = m.get('content', '')[:150]
                    
                    if role == "user":
                        history_text += f"[green]{i}. 👤 You:[/green] {content}\n"
                    elif role in ("assistant", "model"):
                        history_text += f"[blue]{i}. 🤖 Assistant:[/blue] {content}\n"
                    elif role == "tool":
                        tool_name = m.get('name', 'unknown')
                        history_text += f"[yellow]{i}. 🔧 {tool_name}:[/yellow] {content[:100]}...\n"
                
                chat.write(Panel(
                    history_text or "[yellow]No history[/yellow]",
                    title=f"Recent History (Last 10/{len(history)})",
                    border_style="cyan"
                ))
        
        elif cmd == "/state":
            state_text = (
                f"[cyan]Category:[/cyan] {self.state.get('category_to_be_served', 'None')}\n"
                f"[cyan]Query:[/cyan] {self.state.get('query_to_be_served', 'None')}\n"
                f"[cyan]History entries:[/cyan] {len(self.state.get('history', []))}\n"
                f"[cyan]Processing:[/cyan] {self.processing}"
            )
            chat.write(Panel(
                state_text,
                title="Current State",
                border_style="magenta"
            ))
        
        elif cmd == "/help":
            help_text = (
                "[bold cyan]Available Commands:[/bold cyan]\n\n"
                "  • [cyan]/clear[/cyan] - Clear conversation history\n"
                "  • [cyan]/history[/cyan] - Show recent conversation history\n"
                "  • [cyan]/state[/cyan] - Show current application state\n"
                "  • [cyan]/help[/cyan] - Show this help message\n\n"
                "[bold cyan]Keyboard Shortcuts:[/bold cyan]\n\n"
                "  • [cyan]Ctrl+C[/cyan] - Quit application\n"
                "  • [cyan]Ctrl+L[/cyan] - Clear history\n"
                "  • [cyan]Ctrl+H[/cyan] - Show history\n\n"
                "[bold cyan]Available Tools:[/bold cyan]\n\n"
                "  • [green]Mail Agent[/green] - Read, send, manage emails\n"
                "  • [green]Calendar Agent[/green] - Schedule, list, manage events\n"
                "  • [green]Expense Agent[/green] - Track expenses, generate reports"
            )
            chat.write(Panel(
                help_text,
                title="Help",
                border_style="blue"
            ))
        
        else:
            chat.write(Text(f"❌ Unknown command: {command}", style="red"))
    
    async def process_query(self, user_input: str, chat: RichLog) -> None:
        """Process user query through the agent graph."""
        self.processing = True
        
        try:
            # Show processing indicator
            chat.write(Text("⏳ Processing your request...", style="yellow italic"))
            
            # Push user message into history and set query
            self.state = push_history(self.state, "user", user_input)
            self.state["query_to_be_served"] = user_input
            
            # Run through the graph asynchronously
            self.state = await self.graph.ainvoke(self.state)  # type: ignore[assignment]
            
            reply = (self.state.get("response") or "").strip()
            if not reply:
                reply = "I processed your request."
            
            # Display assistant response
            chat.write(Panel(
                Markdown(reply),
                title="[bold blue]🤖 Assistant[/bold blue]",
                border_style="blue"
            ))
            
            # Add assistant reply to history
            self.state = push_history(self.state, "assistant", reply)
            
        except Exception as e:
            chat.write(Panel(
                f"[bold red]❌ Error:[/bold red]\n{str(e)}",
                border_style="red"
            ))
            import traceback
            traceback.print_exc()
        
        finally:
            self.processing = False
    
    def action_clear(self) -> None:
        """Clear conversation history (Ctrl+L)."""
        chat = self.query_one("#chat-container", RichLog)
        self.state["history"] = []
        self.state["query_to_be_served"] = ""
        self.state["category_to_be_served"] = ""
        self.state["response"] = ""
        chat.clear()
        chat.write(Panel(
            "[bold green]✅ History cleared![/bold green]",
            border_style="green"
        ))
    
    def action_show_history(self) -> None:
        """Show conversation history (Ctrl+H)."""
        chat = self.query_one("#chat-container", RichLog)
        history = self.state.get("history", [])
        
        if not history:
            chat.write(Panel(
                "[yellow]No conversation history yet.[/yellow]",
                title="History",
                border_style="yellow"
            ))
        else:
            history_text = ""
            for i, m in enumerate(history[-10:], 1):
                role = m.get('role', 'user')
                content = m.get('content', '')[:150]
                
                if role == "user":
                    history_text += f"[green]{i}. 👤 You:[/green] {content}\n"
                elif role in ("assistant", "model"):
                    history_text += f"[blue]{i}. 🤖 Assistant:[/blue] {content}\n"
            
            chat.write(Panel(
                history_text,
                title=f"Recent History (Last 10/{len(history)})",
                border_style="cyan"
            ))


def main() -> None:
    """Run the Personal Assistant app."""
    app = PersonalAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
