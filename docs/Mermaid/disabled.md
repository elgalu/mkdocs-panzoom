# Disabled Panzoom Example

## Example with Panzoom Disabled

This diagram has panzoom disabled via YAML metadata:

```mermaid
---
panzoom: { enabled: false }
---
flowchart LR
    A([Start]) --> B([aws-cli]) --> C([GitHub SSH]) --> D([SSH Keys Added]) --> E([Ready to Connect])
    style A fill:#e1f5fe,stroke:#4f6b7a,color:#111
    style E fill:#d9ead3,stroke:#4c6b4c,color:#111
```

## Example with Panzoom Enabled (Default)

This diagram has panzoom enabled by default:

```mermaid
flowchart TD
    F([Default Behavior]) --> G([Panzoom Enabled])
    style F fill:#fff3e0,stroke:#e65100,color:#111
    style G fill:#e8f5e8,stroke:#2e7d32,color:#111
```

## Example with Explicit Enable

This diagram explicitly enables panzoom:

```mermaid
---
title: Explicitly Enabled
panzoom: { enabled: true }
---
flowchart TB
    H([Explicit Enable]) --> I([Panzoom Active])
    style H fill:#f3e5f5,stroke:#7b1fa2,color:#111
    style I fill:#e0f2f1,stroke:#00695c,color:#111
```
