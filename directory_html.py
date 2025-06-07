import os
import concurrent.futures
import threading

def is_ignored_path(path, ignore_patterns):
    # Split the path into parts and check if any part matches the ignore patterns
    path_parts = path.split(os.sep)
    return any(part in ignore_patterns for part in path_parts)

def process_file(root, file, ignore_patterns):
    if any(file.endswith(pattern) for pattern in ignore_patterns):
        return None

    file_path = os.path.join(root, file)
    content_lines = [f"{file_path}:\n"]
    try:
        with open(file_path, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
            content_lines.append(content)
    except UnicodeDecodeError:
        content_lines.append("<Binary file or unsupported encoding>\n")
    except Exception as e:
        content_lines.append(f"<Error reading file: {e}>\n")
    content_lines.append("\n\n")
    return content_lines

def build_directory_contents(startpath, output_file, ignore_patterns):
    num_workers = os.cpu_count() * 4  # Heuristic for I/O-bound tasks

    contents = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_file = {executor.submit(process_file, root, file, ignore_patterns): file
                          for root, dirs, files in os.walk(startpath)
                          for file in files if not is_ignored_path(root, ignore_patterns)}

        for future in concurrent.futures.as_completed(future_to_file):
            file_content = future.result()
            if file_content is not None:
                contents.extend(file_content)

    with open(output_file, 'w', encoding='utf-8') as out:
        out.writelines(contents)

# Replace 'your/code/repository/path' with the actual path to your code repository
code_repository_path = 'C:\\Users\\zimme\\OneDrive\\Documents\\GitHub\\agilesnipe'
output_file = 'output_main.txt'
ignore_patterns = ['venv', '.py', '.jpg', '.png', '.js', 'docs', '.css', '.gitattributes', '__pycache__', 'instance', 'web_handlers.py', 'tests', 'migrations', '.gitattributes', 'README.md', 'flask_stripe', 'dbc.py', 'run.py', '.git', 'docs', 'directory_markdown.py', '.txt']

build_directory_contents(code_repository_path, output_file, ignore_patterns)

print(f"Directory contents have been written to {output_file}")
