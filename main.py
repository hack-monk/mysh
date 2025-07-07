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


def handle_echo(command: str):
    """Handle the echo command."""
    args = command.split()[1:]
    sys.stdout.write(" ".join(args) + "\n")


def handle_type(command: str):
    """Handle the type command."""
    args = command.split()[1:]
    if not args:
        sys.stdout.write("type: missing argument\n")
        return

    cmd = args[0]
    if cmd in BUILTIN_COMMANDS:
        sys.stdout.write(f"{cmd} is a shell builtin\n")
    elif path := shutil.which(cmd):
        sys.stdout.write(f"{cmd} is {path}\n")
    else:
        sys.stdout.write(f"{cmd}: not found\n")


def handle_command(command: str):
    """Parse and execute the command."""
    if not command:
        return

    cmd = command.split()[0]

    if cmd == "echo":
        handle_echo(command)
    elif cmd == "type":
        handle_type(command)
    elif cmd == "exit":
        sys.stdout.write("Use 'exit 0' to quit.\n")
    elif cmd == "pwd":
        handle_pwd()
    elif cmd == "cd":
        handle_cd(command)
    else:
        #sys.stdout.write(f"{command}: command not found\n")
        run_program(command.split())

def handle_pwd():
    """Handle the pwd command."""
    sys.stdout.write(os.getcwd() + "\n")

def handle_cd(command: str):
    """Handle the cd command."""
    args = command.split()

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


