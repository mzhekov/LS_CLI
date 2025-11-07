#!/usr/bin/env python3
"""
Network Visualization Demo - Different approaches to display relationships
Shows various ways to render network maps with names in the console
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.tree import Tree
import math

console = Console()


# Sample data
profiles = [
    {"id": 1, "name": "Ava Brown", "short": "Ava B."},
    {"id": 2, "name": "Bob Smith", "short": "Bob S."},
    {"id": 3, "name": "Carol Davis", "short": "Carol D."},
    {"id": 4, "name": "Dan Wilson", "short": "Dan W."},
]

companies = [
    {"id": 1, "name": "TechCorp", "short": "Tech"},
    {"id": 2, "name": "InnovateLab", "short": "Inno"},
]

relationships = [
    {"from": "Ava B.", "to": "Bob S.", "type": "mentor", "bidir": False},
    {"from": "Bob S.", "to": "Carol D.", "type": "friend", "bidir": True},
    {"from": "Carol D.", "to": "Dan W.", "type": "colleague", "bidir": True},
]

works_at = [
    {"person": "Ava B.", "company": "Tech"},
    {"person": "Bob S.", "company": "Tech"},
    {"person": "Carol D.", "company": "Inno"},
]


def option1_compact_labels():
    """Option 1: Compact labels next to nodes in circular layout"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 1: Compact Labels (Current + Names)[/]\n"
        "[dim]Names appear next to emoji icons[/]",
        border_style="cyan"
    ))
    console.print()

    width = 100
    height = 25
    center_x = width // 2
    center_y = height // 2
    radius = 18

    # Create canvas
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    all_nodes = []
    for p in profiles:
        all_nodes.append({"name": p["short"], "type": "profile", "icon": "👥"})
    for c in companies:
        all_nodes.append({"name": c["short"], "type": "company", "icon": "🏢"})

    # Position nodes in circle
    positions = []
    for i, node in enumerate(all_nodes):
        angle = (2 * math.pi * i) / len(all_nodes)
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        positions.append((x, y))

    # Draw some connections (simple lines)
    # Ava B. to Bob S.
    x0, y0 = positions[0]
    x1, y1 = positions[1]
    for i in range(10):
        t = i / 10
        x = int(x0 + t * (x1 - x0))
        y = int(y0 + t * (y1 - y0))
        if 0 <= y < height and 0 <= x < width:
            canvas[y][x] = '─'

    # Bob S. to Carol D.
    x0, y0 = positions[1]
    x1, y1 = positions[2]
    for i in range(10):
        t = i / 10
        x = int(x0 + t * (x1 - x0))
        y = int(y0 + t * (y1 - y0))
        if 0 <= y < height and 0 <= x < width:
            canvas[y][x] = '═'

    # Draw nodes with names
    for i, (pos, node) in enumerate(zip(positions, all_nodes)):
        x, y = pos
        if 0 <= y < height:
            # Place icon
            if x < width - 1:
                canvas[y][x] = node["icon"]

            # Place name next to icon
            name = node["name"]
            start_x = x + 3  # Skip emoji (2 chars) + 1 space
            for j, char in enumerate(name):
                if start_x + j < width:
                    canvas[y][start_x + j] = char

    # Render
    map_text = '\n'.join([''.join(row) for row in canvas])
    console.print(map_text)
    console.print("\n[dim]Pros: Compact, clear labels | Cons: Can overlap with dense networks[/]")


def option2_numbered_legend():
    """Option 2: Numbered nodes with legend below"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 2: Numbered Nodes + Legend[/]\n"
        "[dim]Numbers on map, names in legend table[/]",
        border_style="cyan"
    ))
    console.print()

    width = 80
    height = 20
    center_x = width // 2
    center_y = height // 2
    radius = 15

    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    all_nodes = []
    for p in profiles:
        all_nodes.append({"name": p["short"], "type": "profile"})
    for c in companies:
        all_nodes.append({"name": c["short"], "type": "company"})

    # Position nodes
    positions = []
    for i, node in enumerate(all_nodes):
        angle = (2 * math.pi * i) / len(all_nodes)
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        positions.append((x, y))

    # Draw connections
    x0, y0 = positions[0]
    x1, y1 = positions[1]
    for i in range(15):
        t = i / 15
        x = int(x0 + t * (x1 - x0))
        y = int(y0 + t * (y1 - y0))
        if 0 <= y < height and 0 <= x < width:
            canvas[y][x] = '─'

    # Draw numbered nodes
    for i, pos in enumerate(positions):
        x, y = pos
        node_num = str(i + 1)
        if 0 <= y < height and x < width - 2:
            canvas[y][x] = '['
            canvas[y][x + 1] = node_num if len(node_num) == 1 else node_num[0]
            if x + 2 < width:
                canvas[y][x + 2] = ']' if len(node_num) == 1 else node_num[1]

    # Render map
    map_text = '\n'.join([''.join(row) for row in canvas])
    console.print(map_text)

    # Legend
    console.print()
    table = Table(show_header=True, box=box.SIMPLE, border_style="cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Name", style="white")
    table.add_column("Type", style="magenta")

    for i, node in enumerate(all_nodes):
        node_type = "👥 Profile" if node["type"] == "profile" else "🏢 Company"
        table.add_row(str(i + 1), node["name"], node_type)

    console.print(table)
    console.print("\n[dim]Pros: No overlap, clean map | Cons: Need to look up numbers[/]")


def option3_box_drawing():
    """Option 3: Box-drawing characters with names in boxes"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 3: Box-Drawing with Names[/]\n"
        "[dim]Names inside boxes, connected by lines[/]",
        border_style="cyan"
    ))
    console.print()

    # Hierarchical layout
    output = []
    output.append("                    ╔═══════════╗")
    output.append("                    ║  Tech     ║")
    output.append("                    ╚═══════════╝")
    output.append("                      │   │")
    output.append("            ┌─────────┘   └─────────┐")
    output.append("            │                       │")
    output.append("      ╔═══════════╗           ╔═══════════╗")
    output.append("      ║  Ava B.   ║           ║  Bob S.   ║")
    output.append("      ╚═══════════╝           ╚═══════════╝")
    output.append("            │                       ║")
    output.append("            │ mentor               ║ friend")
    output.append("            └───────────────────────╝")
    output.append("                                    │")
    output.append("                              ╔═══════════╗")
    output.append("                              ║ Carol D.  ║")
    output.append("                              ╚═══════════╝")
    output.append("                                    ║")
    output.append("                                    ║")
    output.append("                    ╔═══════════╗   ║")
    output.append("                    ║  Inno     ║───╝")
    output.append("                    ╚═══════════╝")

    console.print('\n'.join(output))
    console.print("\n[dim]Pros: Clear structure, readable | Cons: Takes more space, manual layout[/]")


def option4_tree_view():
    """Option 4: Rich Tree structure"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 4: Tree Structure[/]\n"
        "[dim]Hierarchical tree with Rich library[/]",
        border_style="cyan"
    ))
    console.print()

    tree = Tree("🌐 [bold cyan]Network Map[/]")

    tech = tree.add("🏢 [green]TechCorp[/]")
    tech_ava = tech.add("👥 [cyan]Ava B.[/] (Senior)")
    tech_bob = tech.add("👥 [cyan]Bob S.[/] (Mid-level)")

    inno = tree.add("🏢 [green]InnovateLab[/]")
    inno_carol = inno.add("👥 [cyan]Carol D.[/] (Developer)")

    relationships = tree.add("🔗 [yellow]Relationships[/]")
    relationships.add("Ava B. → [dim]mentors[/] → Bob S.")
    relationships.add("Bob S. ↔ [dim]friends[/] ↔ Carol D.")

    console.print(tree)
    console.print("\n[dim]Pros: Easy to implement, clear hierarchy | Cons: Not geographic/network-like[/]")


def option5_rich_layout():
    """Option 5: Rich Layout with colored boxes"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 5: Grid Layout with Panels[/]\n"
        "[dim]Names in Rich panels with relationship indicators[/]",
        border_style="cyan"
    ))
    console.print()

    # Create a visual grid
    from rich.columns import Columns
    from rich.layout import Layout

    # Row 1: Company
    tech_panel = Panel(
        "[bold white]TechCorp[/]\n[dim]2 employees[/]",
        border_style="green",
        box=box.ROUNDED
    )

    # Row 2: Employees
    ava_panel = Panel(
        "[bold white]Ava B.[/]\n[dim]Senior[/]\n↓ mentor",
        border_style="cyan",
        box=box.ROUNDED,
        width=20
    )

    bob_panel = Panel(
        "[bold white]Bob S.[/]\n[dim]Mid-level[/]\n↔ friend",
        border_style="cyan",
        box=box.ROUNDED,
        width=20
    )

    carol_panel = Panel(
        "[bold white]Carol D.[/]\n[dim]Developer[/]\n@ InnovateLab",
        border_style="cyan",
        box=box.ROUNDED,
        width=20
    )

    dan_panel = Panel(
        "[bold white]Dan W.[/]\n[dim]Manager[/]",
        border_style="cyan",
        box=box.ROUNDED,
        width=20
    )

    console.print(tech_panel, justify="center")
    console.print()
    console.print(Columns([ava_panel, bob_panel, carol_panel, dan_panel], equal=True))

    console.print("\n[dim]Pros: Beautiful, Rich integration | Cons: Less network-like, more static[/]")


def option6_ascii_art():
    """Option 6: Pure ASCII art with names"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 6: ASCII Art Network[/]\n"
        "[dim]Hand-crafted ASCII with strategic name placement[/]",
        border_style="cyan"
    ))
    console.print()

    art = """
                           TechCorp
                          ╱        ╲
                         ╱          ╲
                        ╱            ╲
                    Ava B.          Bob S.
                       │               ║
                       │ mentor        ║ friend
                       │               ║
                       └───────────────╝
                                       │
                                       │
                                   Carol D.
                                       │
                                       │ works at
                                       │
                                   InnovateLab
                                       │
                                       │
                                    Dan W.
    """

    # Add colors
    lines = art.split('\n')
    for line in lines:
        if 'TechCorp' in line or 'InnovateLab' in line:
            console.print(line, style="bold green")
        elif any(name in line for name in ['Ava B.', 'Bob S.', 'Carol D.', 'Dan W.']):
            console.print(line, style="bold cyan")
        else:
            console.print(line, style="dim")

    console.print("\n[dim]Pros: Clean, artistic | Cons: Manual creation, hard to auto-generate[/]")


def option7_matrix_layout():
    """Option 7: Matrix/Grid with names"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 7: Matrix Layout[/]\n"
        "[dim]Nodes placed in grid with connections[/]",
        border_style="cyan"
    ))
    console.print()

    # Create a grid layout
    width = 100
    height = 15
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    # Define positions manually for clarity
    nodes = [
        {"name": "TechCorp", "x": 40, "y": 2, "color": "green"},
        {"name": "Ava B.", "x": 20, "y": 7, "color": "cyan"},
        {"name": "Bob S.", "x": 60, "y": 7, "color": "cyan"},
        {"name": "Carol D.", "x": 40, "y": 12, "color": "cyan"},
        {"name": "InnovateLab", "x": 75, "y": 12, "color": "green"},
    ]

    # Draw connections first
    connections = [
        (40, 2, 20, 7),  # TechCorp to Ava
        (40, 2, 60, 7),  # TechCorp to Bob
        (60, 7, 40, 12), # Bob to Carol
    ]

    for x0, y0, x1, y1 in connections:
        # Simple vertical/horizontal lines
        if x0 == x1:  # Vertical
            for y in range(min(y0, y1), max(y0, y1)):
                if 0 <= y < height:
                    canvas[y][x0] = '│'
        else:
            # Diagonal approximation
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(steps):
                x = int(x0 + (x1 - x0) * i / steps)
                y = int(y0 + (y1 - y0) * i / steps)
                if 0 <= y < height and 0 <= x < width:
                    canvas[y][x] = '╱' if x1 > x0 else '╲'

    # Draw nodes with names
    for node in nodes:
        x, y = node["x"], node["y"]
        name = node["name"]

        # Box around name
        if 0 <= y < height and x < width - len(name) - 4:
            # Top
            for i in range(len(name) + 4):
                if x - 2 + i < width:
                    canvas[y - 1][x - 2 + i] = '─'
            # Bottom
            for i in range(len(name) + 4):
                if x - 2 + i < width:
                    canvas[y + 1][x - 2 + i] = '─'

            # Sides and name
            canvas[y][x - 2] = '│'
            canvas[y][x - 1] = ' '
            for i, char in enumerate(name):
                if x + i < width:
                    canvas[y][x + i] = char
            if x + len(name) < width:
                canvas[y][x + len(name)] = ' '
            if x + len(name) + 1 < width:
                canvas[y][x + len(name) + 1] = '│'

    # Render
    for row in canvas:
        line = ''.join(row)
        console.print(line)

    console.print("\n[dim]Pros: Flexible positioning | Cons: Complex collision detection needed[/]")


def option8_circular_with_labels():
    """Option 8: Enhanced circular layout (RECOMMENDED)"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Option 8: Enhanced Circular Layout (RECOMMENDED)[/]\n"
        "[dim]Improved version of current implementation with better label placement[/]",
        border_style="green"
    ))
    console.print()

    width = 120
    height = 30
    center_x = width // 2
    center_y = height // 2
    radius = 12

    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    all_nodes = []
    for p in profiles:
        all_nodes.append({"name": p["short"], "full": p["name"], "type": "profile", "icon": "👥"})
    for c in companies:
        all_nodes.append({"name": c["short"], "full": c["name"], "type": "company", "icon": "🏢"})

    # Position nodes
    positions = []
    label_positions = []  # Separate positions for labels

    for i, node in enumerate(all_nodes):
        angle = (2 * math.pi * i) / len(all_nodes)

        # Node position
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        positions.append((x, y))

        # Label position (further out)
        label_radius = radius + 6
        label_x = int(center_x + label_radius * math.cos(angle))
        label_y = int(center_y + label_radius * math.sin(angle))
        label_positions.append((label_x, label_y))

    # Draw edges first (in background)
    edges = [
        (0, 1, "─"),  # Ava to Bob
        (1, 2, "═"),  # Bob to Carol (bidirectional)
        (2, 3, "═"),  # Carol to Dan (bidirectional)
        (0, 4, "·"),  # Ava works at Tech
        (1, 4, "·"),  # Bob works at Tech
        (2, 5, "·"),  # Carol works at Inno
    ]

    for from_idx, to_idx, char in edges:
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
    for i, (pos, node) in enumerate(zip(positions, all_nodes)):
        x, y = pos
        if 0 <= y < height and x < width - 1:
            canvas[y][x] = node["icon"]

    # Draw labels (names) at label positions
    for i, (label_pos, node) in enumerate(zip(label_positions, all_nodes)):
        x, y = label_pos
        name = node["name"]

        # Center the name around the label position
        start_x = x - len(name) // 2

        if 0 <= y < height:
            for j, char in enumerate(name):
                char_x = start_x + j
                if 0 <= char_x < width and canvas[y][char_x] == ' ':
                    canvas[y][char_x] = char

    # Render with colors
    from rich.text import Text
    for row in canvas:
        line_text = Text()
        for char in row:
            if char == '👥':
                line_text.append(char, style="cyan")
            elif char == '🏢':
                line_text.append(char, style="green")
            elif char in '═─·':
                line_text.append(char, style="dim yellow")
            else:
                line_text.append(char, style="white")
        console.print(line_text)

    # Add legend below
    console.print()
    legend = Table(show_header=False, box=None, padding=(0, 2))
    legend.add_column(style="cyan")
    legend.add_row("👥 Profile (cyan)  🏢 Company (green)  ─ Direct  ═ Bidirectional  · Works at")
    console.print(legend)

    console.print("\n[dim]Pros: Clear, auto-layout, scalable | Cons: Label overlap in dense networks[/]")


# Run all demos
def main():
    console.print("\n")
    console.print(Panel(
        "[bold white]Network & Relationships Map - Visualization Options[/]\n"
        "[dim]Comparing different approaches to display network maps with names[/]",
        border_style="bold cyan",
        box=box.DOUBLE
    ))

    option1_compact_labels()
    option2_numbered_legend()
    option3_box_drawing()
    option4_tree_view()
    option5_rich_layout()
    option6_ascii_art()
    option7_matrix_layout()
    option8_circular_with_labels()

    # Summary
    console.print("\n" * 2)
    console.print(Panel(
        "[bold green]Summary & Recommendations[/]\n\n"
        "[bold cyan]Best for Dynamic Data:[/] Option 8 (Enhanced Circular)\n"
        "[dim]- Auto-layout with clear labels\n"
        "[dim]- Scales with network size\n"
        "[dim]- Easy to implement\n\n"
        "[bold cyan]Best for Hierarchies:[/] Option 4 (Tree View)\n"
        "[dim]- Perfect for org charts\n"
        "[dim]- Rich library integration\n\n"
        "[bold cyan]Best for Small Networks:[/] Option 3 (Box Drawing)\n"
        "[dim]- Very clear and readable\n"
        "[dim]- Professional appearance\n\n"
        "[bold cyan]Most Flexible:[/] Option 7 (Matrix Layout)\n"
        "[dim]- Custom positioning\n"
        "[dim]- Good for complex relationships\n",
        border_style="bold green",
        title="🎯 Recommendations"
    ))


if __name__ == "__main__":
    main()
