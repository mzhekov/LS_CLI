#!/usr/bin/env python3
"""
Test of the new relationship-based network map
"""

from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.text import Text

console = Console()


def shorten_name(name, max_len=15):
    """Shorten name to fit in box"""
    if len(name) <= max_len:
        return name
    parts = name.split()
    if len(parts) > 1:
        return f"{parts[0]} {parts[-1][0]}."[:max_len]
    return name[:max_len]


def create_box(text, width=None):
    """Create a box around text"""
    if width is None:
        width = len(text) + 2
    else:
        width = max(width, len(text) + 2)

    padding = (width - 2 - len(text)) // 2
    text_line = f"║ {' ' * padding}{text}{' ' * (width - 2 - len(text) - padding)} ║"

    top = f"╔{'═' * (width - 2)}╗"
    bottom = f"╚{'═' * (width - 2)}╝"

    return [top, text_line, bottom]


# Sample relationships
relationships = [
    {"from": "dfsfs fsd fsd", "to": "esd sdfsdfs", "type": "Manages", "bidir": True, "status": "Bad"},
    {"from": "dfsfs fsd fsd", "to": "esd sdfsdfs", "type": "Mentor", "bidir": True, "status": "Good"},
    {"from": "Ava Johnson", "to": "Avery Wilson", "type": "Friend", "bidir": True, "status": "Good"},
    {"from": "Alexander Kim", "to": "Brian Thompson", "type": "Client", "bidir": True, "status": "Good"},
]

print("\n=== New Relationship-Based Network Map ===\n")

map_lines = []

for rel in relationships:
    from_name = shorten_name(rel["from"], 15)
    to_name = shorten_name(rel["to"], 15)
    rel_type = rel["type"][:12]

    # Determine arrow and status
    if rel["bidir"]:
        arrow = "═══"
        connector = "═══"
    else:
        arrow = "───"
        connector = "───>"

    # Status indicator
    if rel["status"] == "Bad":
        status_mark = "✗"
    elif rel["status"] == "Good":
        status_mark = "✓"
    else:
        status_mark = "○"

    # Draw FROM box
    from_box = create_box(f"👥 {from_name}", 20)
    for line in from_box:
        map_lines.append(line.center(100))

    # Draw relationship connection
    if rel["bidir"]:
        rel_line = f"{arrow}[{rel_type} {status_mark}]{arrow}"
    else:
        rel_line = f"{connector}[{rel_type} {status_mark}]"
    map_lines.append(rel_line.center(100))

    # Draw TO box
    to_box = create_box(f"👥 {to_name}", 20)
    for line in to_box:
        map_lines.append(line.center(100))

    map_lines.append("")  # Spacing

map_text = '\n'.join(map_lines)

# Add legend
legend = Text()
legend.append("👥 Profile", style="cyan")
legend.append("  ", style="dim")
legend.append("🏢 Company", style="green")
legend.append("  ", style="dim")
legend.append("───> Direct", style="dim")
legend.append("  ", style="dim")
legend.append("═══ Bidirectional", style="dim")
legend.append("  ", style="dim")
legend.append("✓ Good", style="green")
legend.append("  ", style="dim")
legend.append("✗ Bad", style="red")

console.print(Panel(
    map_text,
    title="[bold cyan]Network Map - Relationship View[/]",
    subtitle=legend,
    border_style="cyan",
    box=box.SIMPLE
))

print("\n✓ New relationship-based visualization!")
print("Each relationship is shown visually with:")
print("  - Boxes for each person/company")
print("  - Labeled connection showing relationship type")
print("  - Status indicator (✓ Good, ✗ Bad)")
print("  - Arrow direction (───> one-way, ═══ two-way)\n")
