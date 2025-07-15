import sys
import shutil
import subprocess
import os
import readline
import io

BUILTIN_COMMANDS = ["exit", "echo", "type", "pwd", "cd", "history"]
command_history = []
last_completion = {"prefix": "", "count": 0}
last_tab_text = ""
last_tab_matches = []
last_tab_count = 0

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
    if not command:
        return
    
    if '|' in command:
        run_pipeline(command)
        return
    
    args = parse_command(command)
    
    if not args:
        return

    cmd = args[0]

    
    command_history.append(command)

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
    elif cmd == "history":
        handle_history(args[1:])
    else:
        run_program(args)

def handle_history(args=None):
    """Print the command history with line numbers. Optionally limit entries using history <n>."""
    try:
        # Default: show all history
        limit = None

        # If an argument is passed, try converting it to an integer
        if args and len(args) == 1:
            limit = int(args[0])

        start_index = max(len(command_history) - limit, 0) if limit is not None else 0
        sliced_history = command_history[start_index:]

        for idx, entry in enumerate(sliced_history, start_index + 1):
            print(f"    {idx}  {entry}")

    except ValueError:
        print("history: invalid number")


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


def get_executable_matches(text):
    matches = []

    # Built-ins
    for cmd in BUILTIN_COMMANDS:
        if cmd.startswith(text):
            matches.append(cmd)

    # Executables in PATH
    seen = set(matches)
    for dir_path in os.environ.get("PATH", "").split(os.pathsep):
        if not os.path.isdir(dir_path):
            continue
        try:
            for entry in os.listdir(dir_path):
                if entry.startswith(text):
                    full_path = os.path.join(dir_path, entry)
                    if os.access(full_path, os.X_OK) and entry not in seen:
                        matches.append(entry)
                        seen.add(entry)
        except Exception:
            continue

    return sorted(matches)


def get_longest_common_prefix(strings):
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings[1:]:
        i = 0
        while i < len(prefix) and i < len(s) and prefix[i] == s[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def completer(text, state):
    global last_tab_text, last_tab_matches, last_tab_count

    buffer = readline.get_line_buffer()
    cursor_pos = readline.get_begidx()

    # Only autocomplete the first word (command name)
    if cursor_pos > 0:
        return None

    # Reset if new input
    if text != last_tab_text:
        last_tab_text = text
        last_tab_matches = get_executable_matches(text)
        last_tab_count = 0

    # No matches
    if not last_tab_matches:
        return None

    # Only one match → return it
    if len(last_tab_matches) == 1:
        if state == 0:
            last_tab_count = 0
            return last_tab_matches[0] + " "
        return None

    # Compute LCP of all matches
    lcp = get_longest_common_prefix(last_tab_matches)

    # If LCP is longer than current text → complete it
    if len(lcp) > len(text):
        if state == 0:
            last_tab_text = lcp
            return lcp
        return None

    # If LCP == text → multiple matches, handle bell or list
    if last_tab_count == 0:
        last_tab_count += 1
        if state == 0:
            sys.stdout.write("\a")  # Bell
            sys.stdout.flush()
        return None
    else:
        if state == 0:
            print()
            print("  ".join(last_tab_matches))
            sys.stdout.write(f"$ {text}")
            sys.stdout.flush()
        return None


def run_pipeline(command: str):
    stages = [stage.strip() for stage in command.split('|')]
    n = len(stages)

    if n < 2:
        sys.stdout.write("Pipeline must have at least two commands.\n")
        return

    commands_list = [parse_command(stage) for stage in stages]
    if any(not cmd for cmd in commands_list):
        sys.stdout.write("Invalid pipeline command.\n")
        return

    processes = []
    prev_read_fd = None
    pipe_fds = []

    for i, args in enumerate(commands_list):
        is_builtin = args[0] in BUILTIN_COMMANDS

        # Create pipe for next stage if not the last command
        if i < n - 1:
            read_fd, write_fd = os.pipe()
            pipe_fds.append((read_fd, write_fd))
        else:
            read_fd, write_fd = None, None

        pid = os.fork()
        if pid == 0:
            # Child process

            # If there's a previous read end, set it as stdin
            if prev_read_fd is not None:
                os.dup2(prev_read_fd, 0)
            # If there's a write end, set it as stdout
            if write_fd is not None:
                os.dup2(write_fd, 1)

            # Close all pipe fds in the child
            for r, w in pipe_fds:
                try:
                    os.close(r)
                    os.close(w)
                except:
                    pass

            if is_builtin:
                run_builtin(args)
                os._exit(0)
            else:
                try:
                    os.execvp(args[0], args)
                except FileNotFoundError:
                    sys.stdout.write(f"{args[0]}: command not found\n")
                    os._exit(1)
        else:
            processes.append(pid)
            # Parent process: close fds that are no longer needed
            if prev_read_fd is not None:
                os.close(prev_read_fd)
            if write_fd is not None:
                os.close(write_fd)

            # Update prev_read_fd to current stage's read_fd for next command
            prev_read_fd = read_fd

    # Close any remaining fds in parent
    for r, w in pipe_fds:
        try:
            os.close(r)
            os.close(w)
        except:
            pass

    # Wait for all processes
    for pid in processes:
        os.waitpid(pid, 0)


def run_builtin(args):
    if args[0] == "echo":
        handle_echo(args)
    elif args[0] == "type":
        handle_type(args)
    elif args[0] == "pwd":
        handle_pwd()
    elif args[0] == "cd":
        handle_cd(args)
    elif args[0] == "exit":
        sys.exit(0)

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
    
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')

    while True:
        try:
            command = input("$ ")  # Pass prompt directly here
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if handle_exit(command.strip()):
            break

        handle_command(command)

if __name__ == "__main__":
    main()


