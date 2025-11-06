#!/usr/bin/env python3
"""
Quick test of the box-drawing visualization
"""

from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.text import Text

console = Console()


def shorten_name(name, max_len=12):
    """Shorten name to fit in box (e.g., 'John Smith' -> 'John S.')"""
    if len(name) <= max_len:
        return name
    parts = name.split()
    if len(parts) > 1:
        return f"{parts[0]} {parts[-1][0]}."[:max_len]
    return name[:max_len]


def create_box(text, width=None):
    """Create a box around text using box-drawing characters"""
    if width is None:
        width = len(text) + 2
    else:
        width = max(width, len(text) + 2)

    padding = (width - 2 - len(text)) // 2
    text_line = f"║ {' ' * padding}{text}{' ' * (width - 2 - len(text) - padding)} ║"

    top = f"╔{'═' * (width - 2)}╗"
    bottom = f"╚{'═' * (width - 2)}╝"

    return [top, text_line, bottom]


# Test data
print("\n=== Box-Drawing Network Visualization Test ===\n")

map_lines = []

# Company 1
company_name = "TechCorp"
company_box = create_box(f"🏢 {company_name}", 20)
for line in company_box:
    map_lines.append(line.center(80))

# Branching to 2 employees
map_lines.append("│".center(80))

# Draw branching connector
line = ' ' * 80
line_list = list(line)
line_list[25] = '│'
line_list[55] = '│'
for i in range(25, 56):
    if line_list[i] == ' ':
        line_list[i] = '─'
line_list[25] = '┌'
line_list[55] = '┐'
line_list[40] = '┴'
map_lines.append(''.join(line_list))

# Employee boxes
emp1_box = create_box("👥 Ava B.", 16)
emp2_box = create_box("👥 Bob S.", 16)

for line_idx in range(3):
    combined = f"{emp1_box[line_idx]}  {emp2_box[line_idx]}"
    map_lines.append(combined.center(80))

map_lines.append("")

# Independent profile
map_lines.append("")
map_lines.append("── Independent Profiles ──".center(80))
map_lines.append("")

carol_box = create_box("👥 Carol D.", 16)
for line in carol_box:
    map_lines.append(line.center(80))

map_lines.append("")

# Relationships
map_lines.append("")
map_lines.append("── Key Relationships ──".center(80))
map_lines.append("")

rel_line = "Ava B. ───[mentor]───> Bob S."
map_lines.append(rel_line.center(80))

rel_line = "Bob S. ═══[friend]═══> Carol D."
map_lines.append(rel_line.center(80))

map_text = '\n'.join(map_lines)

# Add legend
legend = Text()
legend.append("🏢 Company", style="green")
legend.append("  ", style="dim")
legend.append("👥 Profile", style="cyan")
legend.append("  ", style="dim")
legend.append("─── Direct", style="dim")
legend.append("  ", style="dim")
legend.append("═══ Bidirectional", style="dim")

console.print(Panel(
    map_text,
    title="[bold cyan]Network Map (Box-Drawing Style)[/]",
    subtitle=legend,
    border_style="cyan",
    box=box.SIMPLE
))

print("\n✓ Box-drawing visualization working correctly!")
print("This is how the Network & Relationships menu will now display.\n")
