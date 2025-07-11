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
    args, stdout_redirect, stderr_redirect = split_redirect(args)
    output = " ".join(args[1:]) + "\n"

    try:
        out_target = open(stdout_redirect[0], stdout_redirect[1]) if stdout_redirect else None
        err_target = open(stderr_redirect[0], stderr_redirect[1]) if stderr_redirect else None

        if out_target:
            out_target.write(output)
        else:
            sys.stdout.write(output)

        if err_target:
            pass  # ensure file is created even if unused

        if out_target:
            out_target.close()
        if err_target:
            err_target.close()

    except Exception as e:
        sys.stdout.write(f"echo: error writing to file: {e}\n")


def handle_type(args: list[str]):
    args, stdout_file, stderr_file = split_redirect(args)

    if len(args) < 2:
        output = "type: missing argument\n"
    else:
        cmd = args[1]
        if cmd in BUILTIN_COMMANDS:
            output = f"{cmd} is a shell builtin\n"
        elif path := shutil.which(cmd):
            output = f"{cmd} is {path}\n"
        else:
            output = f"{cmd}: not found\n"

    if stdout_file:
        with open(stdout_file, 'w') as f:
            f.write(output)
    else:
        sys.stdout.write(output)


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

def split_redirect(args: list[str]) -> tuple[list[str], tuple[str, str] | None, tuple[str, str] | None]:
    """
    Splits args and returns:
      - cleaned args
      - stdout redirection: (filename, mode) or None
      - stderr redirection: (filename, mode) or None
    """
    stdout_redirect = None
    stderr_redirect = None
    new_args = []

    i = 0
    while i < len(args):
        if args[i] in ('>', '1>'):
            if i + 1 < len(args):
                stdout_redirect = (args[i + 1], 'w')  # overwrite
                i += 2
                continue
            else:
                sys.stdout.write("Syntax error: no file for stdout redirection\n")
                return args, None, None

        elif args[i] in ('>>', '1>>'):
            if i + 1 < len(args):
                stdout_redirect = (args[i + 1], 'a')  # append
                i += 2
                continue
            else:
                sys.stdout.write("Syntax error: no file for stdout append\n")
                return args, None, None

        elif args[i] == '2>':
            if i + 1 < len(args):
                stderr_redirect = (args[i + 1], 'w')  # overwrite
                i += 2
                continue
            else:
                sys.stdout.write("Syntax error: no file for stderr redirection\n")
                return args, None, None

        elif args[i] == '2>>':
            if i + 1 < len(args):
                stderr_redirect = (args[i + 1], 'a')  # append
                i += 2
                continue
            else:
                sys.stdout.write("Syntax error: no file for stderr append\n")
                return args, None, None

        else:
            new_args.append(args[i])
            i += 1

    return new_args, stdout_redirect, stderr_redirect


def run_program(args: list[str]):
    """Run an external command with redirection support."""
    args, stdout_redirect, stderr_redirect = split_redirect(args)

    if not args:
        return

    executable = shutil.which(args[0])

    if executable:
        try:
            stdout_target = open(stdout_redirect[0], stdout_redirect[1]) if stdout_redirect else None
            stderr_target = open(stderr_redirect[0], stderr_redirect[1]) if stderr_redirect else None

            subprocess.run(
                args,
                stdout=stdout_target or sys.stdout,
                stderr=stderr_target or sys.stderr
            )

            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

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


