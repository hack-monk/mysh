import sys
import shutil
import subprocess
import os

BUILTIN_COMMANDS = ["exit", "echo", "type", "pwd", "cd"]

def prompt():
    """Display the shell prompt."""
    sys.stdout.write("$ ")
    sys.stdout.flush()

def handle_exit(command: str) -> bool:
    """Handle the exit command."""
    return command.strip() == "exit 0"

def handle_echo(args: list[str]):
    """Handle the echo command."""
    #args = command.split()[1:]
    #sys.stdout.write(" ".join(args) + "\n")
    sys.stdout.write(" ".join(args[1:]) + "\n")

def handle_type(args: list[str]):
    """Handle the type command."""
    #args = command.split()[1:]
    if  len(args) < 2:
        sys.stdout.write("type: missing argument\n")
        return

    cmd = args[1]

    if cmd in BUILTIN_COMMANDS:
        sys.stdout.write(f"{cmd} is a shell builtin\n")
    elif path := shutil.which(cmd):
        sys.stdout.write(f"{cmd} is {path}\n")
    else:
        sys.stdout.write(f"{cmd}: not found\n")

def handle_command(command: str):
    """Parse and execute the command."""
    args = parse_command(command)
    if not args:
        return

    cmd = args[0]

    if cmd == "echo":
        handle_echo(args)
    elif cmd == "type":
        handle_type(args)
    elif cmd == "exit":
        sys.stdout.write("Use 'exit 0' to quit.\n")
    elif cmd == "pwd":
        handle_pwd()
    elif cmd == "cd":
        handle_cd(args)
    else:
        #sys.stdout.write(f"{command}: command not found\n")
        run_program(args)

def handle_pwd():
    """Handle the pwd command."""
    sys.stdout.write(os.getcwd() + "\n")

def handle_cd(args: list[str]):
    """Handle the cd command."""
    #args = command.split()
    if len(args) != 2:
        sys.stdout.write("cd: missing argument\n")
        return

    path = args[1]

    if path.startswith("~"):
        home_dir = os.environ.get("HOME")
        if not home_dir:
            sys.stdout.write("cd: HOME environment variable not set\n")
            return
        path = os.path.expanduser(path)  # handles ~ and ~/subdir correctly


    new_path = os.path.abspath(path)

    try:
        os.chdir(new_path)
    except FileNotFoundError:
        sys.stdout.write(f"cd: {path}: No such file or directory\n")
    except NotADirectoryError:
        sys.stdout.write(f"cd: {path}: Not a directory\n")

def parse_command(command: str) -> list:
    """Parse shell command handling single and double quotes correctly."""
    args = []
    current = ''
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(command):
        char = command[i]

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue
        elif char == '\\':
            # Backslash escape logic
            i += 1
            if i >= len(command):
                # Trailing backslash — treat as literal
                current += '\\'
                break
            next_char = command[i]

            if in_single_quote:
                # In single quotes, backslash is literal
                current += '\\' + next_char
            elif in_double_quote:
                # Only escape ", \, $, ` inside double quotes
                if next_char in ['\\', '"', '$', '`']:
                    current += next_char
                else:
                    current += '\\' + next_char
            else:
                # Outside quotes — backslash escapes any char
                current += next_char
            i += 1
            continue

        elif char.isspace() and not in_single_quote and not in_double_quote:
            if current:
                args.append(current)
                current = ''
        else:
            current += char
        i += 1

    if current:
        args.append(current)

    return args


def run_program(args: list[str]):
    """Run an external command with arguments using subprocess."""

    executable = shutil.which(args[0])

    if executable:
        try:
            result = subprocess.run(args, check=False)
        except Exception as e:
            sys.stdout.write(f"Error executing command: {e}\n")
    else:
        sys.stdout.write(f"{args[0]}: command not found\n")

def main():
    """Main REPL loop."""
    while True:
        prompt()

        try:
            command = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if handle_exit(command):
            break

        handle_command(command)

if __name__ == "__main__":
    main()


