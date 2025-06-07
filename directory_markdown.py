import os
import concurrent.futures
import threading
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_ignored_path(path, ignore_patterns):
    path_parts = path.split(os.sep)
    return any(part in ignore_patterns for part in path_parts)

def process_file(root, file, ignore_patterns, output_dir):
    if any(file.endswith(pattern) for pattern in ignore_patterns):
        return None

    file_path = os.path.join(root, file)
    relative_path = os.path.relpath(file_path, start=os.path.dirname(output_dir))
    markdown_file = os.path.join(output_dir, f"{relative_path}.md")
    os.makedirs(os.path.dirname(markdown_file), exist_ok=True)

    try:
        with open(file_path, 'rb') as content_file:  # Open as binary
            if is_binary(content_file.peek()):
                # Copy binary file directly to the output directory
                binary_output_path = os.path.join(output_dir, relative_path)
                os.makedirs(os.path.dirname(binary_output_path), exist_ok=True)
                shutil.copy(file_path, binary_output_path)
                logging.info(f"Copied binary file: {file_path}")
                return relative_path
            else:
                content_file.seek(0)  # Reset file pointer after peek
                content = content_file.read().decode('utf-8')
                with open(markdown_file, 'w', encoding='utf-8') as md_file:
                    md_file.write(f"# {relative_path}\n\n```\n{content}\n```\n")
                    return relative_path
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
    return None

def is_binary(data):
    # A simple heuristic to check if a file is binary
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(data.translate(None, textchars))

def build_directory_contents(startpath, output_dir, ignore_patterns):
    num_workers = os.cpu_count() * 4

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    summary_file = os.path.join(output_dir, 'SUMMARY.md')
    contents = ["# Directory Summary\n\n"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_file = {
            executor.submit(process_file, root, file, ignore_patterns, output_dir): file
            for root, dirs, files in os.walk(startpath)
            for file in files if not is_ignored_path(root, ignore_patterns)
        }

        for future in concurrent.futures.as_completed(future_to_file):
            relative_path = future.result()
            if relative_path is not None:
                contents.append(f"- [{relative_path}]({relative_path}.md)\n")

    with open(summary_file, 'w', encoding='utf-8') as out:
        out.writelines(contents)

    logging.info(f"Directory summary has been written to {summary_file}")

# Replace 'your/code/repository/path' with the actual path to your code repository
code_repository_path = 'C:\\Users\\zimme\\Downloads\\agilesnipe-main\\agilesnipe-main'
output_dir = 'directory_structure'
ignore_patterns = ['venv', '__pycache__', 'instance', 'migrations', '.gitattributes', '.git', 'directory_ai.py', 'web_handlers.py', 'docs', 'run.py', 'dbc.py', 'tests', 'static']

build_directory_contents(code_repository_path, output_dir, ignore_patterns)
