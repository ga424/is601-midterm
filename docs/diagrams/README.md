# Diagram Rendering Guide

These files are the Mermaid source files for architecture diagrams:

- `c4-context.mmd`
- `c4-container.mmd`
- `c4-component-core.mmd`
- `code-summary.mmd`
- `deployment-view.mmd`

## How to preview in VS Code

1. Open one `.mmd` file.
2. Run `Mermaid: Open Preview`.

## Common error and fix

If you see:

`Lexical error ... Unrecognized text. # C4 Architecture ...`

you are previewing `docs/c4-architecture.md` with Mermaid Preview. Use Markdown Preview for that file, and Mermaid Preview only for `.mmd` files.
