---
mark_as_read: { updated_at: 2025-09-05 12:35:05+02:00 }
---

# Smart Panzoom Auto-Detection

The plugin now automatically detects diagram size/complexity and only enables panzoom for larger diagrams that would benefit from zoom functionality.

## Small Diagrams with 5 nodes

```mermaid
flowchart LR
    A([Start]) --> B([aws-cli]) --> C([GitHub SSH]) --> D([SSH Keys Added]) --> E([Ready to Connect])
```

## Small Diagrams (Auto-Disabled)

Small/simple diagrams automatically have panzoom disabled since they don't need zoom functionality:

```mermaid
flowchart LR
    A([Start]) --> B([End])
```

## Large Diagrams (Auto-Enabled)

Complex diagrams automatically get panzoom enabled:

```mermaid
flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]
    I[Additional Node] --> J[Another Node]
    K[Yet Another] --> L[Final Node]
```

## Manual Override: Force Disable

You can explicitly disable panzoom even for large diagrams:

```mermaid
---
panzoom: { enabled: false }
---
flowchart LR
    A([Start]) --> B([aws-cli]) --> C([GitHub SSH]) --> D([SSH Keys Added]) --> E([Ready to Connect])
    style A fill:#e1f5fe,stroke:#4f6b7a,color:#111
    style E fill:#d9ead3,stroke:#4c6b4c,color:#111
```

## Manual Override: Force Enable

You can explicitly enable panzoom even for small diagrams:

```mermaid
---
panzoom: { enabled: true }
---
flowchart LR
    A --> B --> C
```

## Configuration Options

You can customize the auto-detection thresholds in your `mkdocs.yml`:

```yaml
plugins:
  - panzoom:
      # Enable/disable smart auto-detection
      auto_enable: true  # default: true

      # Customize thresholds for auto-detection
      auto_enable_threshold_lines: 8    # default: 8 lines
      auto_enable_threshold_nodes: 6    # default: 6 nodes
      auto_enable_threshold_edges: 5    # default: 5 connections
      auto_enable_threshold_chars: 200  # default: 200 characters

      # Other existing options...
      show_zoom_buttons: true
      full_screen: true
```

## How It Works

The plugin analyzes each Mermaid diagram and counts:

- **Lines**: Number of non-empty lines in the diagram code
- **Nodes**: Number of elements (boxes, circles, decision points, etc.)
- **Edges**: Number of connections/arrows between elements
- **Characters**: Total character count of the diagram

If any metric exceeds its threshold, panzoom is automatically enabled. You can always override this behavior using explicit YAML metadata.

## Legacy Behavior

To disable auto-detection and enable panzoom for all diagrams (old behavior):

```yaml
plugins:
  - panzoom:
      auto_enable: false  # Disables smart detection
```
