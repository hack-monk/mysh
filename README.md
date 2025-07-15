# 🐚 Mysh – A Custom Shell in Python

Mysh is a Python-based interactive shell built from scratch. It supports command execution, tab completion, pipelines, and persistent command history, offering a simplified shell experience with features similar to traditional Unix shells.

## 🚀 Features

- ✅ Execute built-in and external commands
- 🔁 Tab completion for:
  - Built-in commands
  - Executables in `PATH`
  - Longest common prefix completion
  - Multi-match and bell notification handling
- 🧵 Pipelines:
  - Dual and multi-command pipelines
  - Support for built-ins in pipelines
- 🧠 Command history:
  - View with `history`
  - Limit output using `history <n>`
  - Load from file: `history -r <file>`
  - Write to file: `history -w <file>`
  - Append new entries: `history -a <file>`
  - Auto load/save using the `HISTFILE` environment variable

## 🛠️ Built-in Commands

- `echo`
- `type`
- `history`
- `exit 0`

## 📁 Files

- `main.py` – Main implementation of Mysh
- `README.md` – This file

## 💻 Running Mysh

```bash
python3 main.py
