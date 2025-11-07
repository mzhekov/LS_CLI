#!/usr/bin/env python3
"""
Test of the Enhanced Circular Layout (Option 8)
"""

from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.text import Text
import math

console = Console()


def shorten_name(name, max_len=10):
    """Shorten name to fit"""
    if len(name) <= max_len:
        return name
    parts = name.split()
    if len(parts) > 1:
        return f"{parts[0]} {parts[-1][0]}."[:max_len]
    return name[:max_len]


# Sample data - 6 people with relationships
people = [
    {"id": 1, "name": "Ava Johnson", "icon": "👥"},
    {"id": 2, "name": "Bob Smith", "icon": "👥"},
    {"id": 3, "name": "Carol Davis", "icon": "👥"},
    {"id": 4, "name": "Dan Wilson", "icon": "👥"},
    {"id": 5, "name": "Eve Martinez", "icon": "👥"},
    {"id": 6, "name": "Frank Lee", "icon": "👥"},
]

relationships = [
    {"from": 1, "to": 2, "bidir": False},   # Ava → Bob
    {"from": 2, "to": 3, "bidir": True},    # Bob ↔ Carol
    {"from": 3, "to": 4, "bidir": True},    # Carol ↔ Dan
    {"from": 4, "to": 5, "bidir": False},   # Dan → Eve
    {"from": 5, "to": 6, "bidir": True},    # Eve ↔ Frank
    {"from": 6, "to": 1, "bidir": False},   # Frank → Ava (closes circle)
]

print("\n=== Enhanced Circular Layout Test ===\n")

# Layout settings
width = 120
height = 35
center_x = width // 2
center_y = height // 2
radius = 14

# Shorten names
nodes = []
for person in people:
    nodes.append({
        'id': person['id'],
        'name': shorten_name(person['name'], 10),
        'icon': person['icon']
    })

# Position nodes in circle
positions = []
label_positions = []

for i, node in enumerate(nodes):
    angle = (2 * math.pi * i) / len(nodes)

    # Node position (on circle)
    x = int(center_x + radius * math.cos(angle))
    y = int(center_y + radius * math.sin(angle))
    positions.append((x, y))

    # Label position (further out)
    label_radius = radius + 8
    label_x = int(center_x + label_radius * math.cos(angle))
    label_y = int(center_y + label_radius * math.sin(angle))
    label_positions.append((label_x, label_y))

# Create canvas
canvas = [[' ' for _ in range(width)] for _ in range(height)]

# Draw edges (relationships)
for rel in relationships:
    from_idx = rel['from'] - 1
    to_idx = rel['to'] - 1

    x0, y0 = positions[from_idx]
    x1, y1 = positions[to_idx]

    # Bresenham's line algorithm
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0
    steps = 0
    max_steps = 200

    char = '═' if rel['bidir'] else '─'

    while steps < max_steps:
        if 0 <= y < height and 0 <= x < width:
            if canvas[y][x] == ' ':
                canvas[y][x] = char

        if x == x1 and y == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

        steps += 1

# Draw nodes (icons)
for i, (pos, node) in enumerate(zip(positions, nodes)):
    x, y = pos
    if 0 <= y < height and x < width - 1:
        canvas[y][x] = node['icon']

# Draw labels (names)
for i, (label_pos, node) in enumerate(zip(label_positions, nodes)):
    x, y = label_pos
    name = node['name']

    # Center the name
    start_x = x - len(name) // 2

    if 0 <= y < height:
        for j, char in enumerate(name):
            char_x = start_x + j
            if 0 <= char_x < width and canvas[y][char_x] == ' ':
                canvas[y][char_x] = char

# Render with colors
map_lines = []
for row in canvas:
    line_parts = []
    for char in row:
        if char == '👥':
            line_parts.append(f"[cyan]{char}[/cyan]")
        elif char in '═─':
            line_parts.append(f"[dim yellow]{char}[/dim yellow]")
        else:
            line_parts.append(char)
    map_lines.append(''.join(line_parts))

map_text = '\n'.join(map_lines)

# Legend
legend = Text()
legend.append("👥 Profile", style="cyan")
legend.append("  ", style="dim")
legend.append("─ Direct", style="dim yellow")
legend.append("  ", style="dim")
legend.append("═ Bidirectional", style="dim yellow")

console.print(Panel(
    map_text,
    title="[bold cyan]Network Map - Enhanced Circular Layout[/]",
    subtitle=legend,
    border_style="cyan",
    box=box.SIMPLE
))

print("\n✓ Circular layout with:")
print("  - Nodes positioned in a circle")
print("  - Names placed outside the circle for readability")
print("  - Lines connecting related nodes")
print("  - Different line styles (─ direct, ═ bidirectional)\n")
