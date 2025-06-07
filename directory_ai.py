import os
import concurrent.futures
import threading
import logging
from pathlib import Path
from typing import List, Optional, Set

# Configure logging for better debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_ignored_path(path: str, ignore_dirs: Set[str], ignore_extensions: Set[str]) -> bool:
    """
    Check if a path should be ignored based on directory names or file extensions.
    
    Args:
        path: The file or directory path to check
        ignore_dirs: Set of directory names to ignore
        ignore_extensions: Set of file extensions to ignore (including dot, e.g., '.txt')
    
    Returns:
        bool: True if the path should be ignored
    """
    path_obj = Path(path)
    
    # Check if any directory in the path matches ignore_dirs
    if any(part in ignore_dirs for part in path_obj.parts):
        logger.debug(f"Ignoring path {path} due to directory match")
        return True
    
    # Check file extension
    if path_obj.suffix.lower() in ignore_extensions:
        logger.debug(f"Ignoring path {path} due to extension {path_obj.suffix}")
        return True
    
    logger.debug(f"Path {path} is not ignored")
    return False

def process_file(root: str, file: str, ignore_dirs: Set[str], ignore_extensions: Set[str]) -> Optional[List[str]]:
    """
    Process a single file and return its contents with metadata.
    
    Args:
        root: Directory path containing the file
        file: Name of the file to process
        ignore_dirs: Set of directories to ignore
        ignore_extensions: Set of file extensions to ignore
    
    Returns:
        Optional[List[str]]: File contents with metadata or None if ignored
    """
    file_path = os.path.join(root, file)
    
    if is_ignored_path(file_path, ignore_dirs, ignore_extensions):
        logger.debug(f"Skipping ignored file: {file_path}")
        return None

    content_lines = [f"{file_path}:\n"]
    logger.debug(f"Processing file: {file_path}")
    try:
        # Only process text files smaller than 10MB
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            content_lines.append("<File too large to process>\n")
            logger.debug(f"File too large: {file_path}")
            return content_lines
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as content_file:
            content = content_file.read()
            content_lines.append(content)
            logger.debug(f"Successfully read file: {file_path}")
    except UnicodeDecodeError:
        content_lines.append("<Binary file or unsupported encoding>\n")
        logger.debug(f"Binary or unsupported encoding: {file_path}")
    except PermissionError:
        content_lines.append("<Permission denied>\n")
        logger.debug(f"Permission denied: {file_path}")
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        content_lines.append(f"<Error reading file: {e}>\n")
    
    content_lines.append("\n\n")
    return content_lines

def build_directory_contents(startpath: str, output_file: str, 
                           ignore_dirs: Set[str], ignore_extensions: Set[str]) -> None:
    """
    Build directory contents and write to output file using concurrent processing.
    
    Args:
        startpath: Root directory to start scanning
        output_file: Output file path
        ignore_dirs: Set of directories to ignore
        ignore_extensions: Set of file extensions to ignore
    """
    # Validate input path
    start_path = Path(startpath)
    if not start_path.exists() or not start_path.is_dir():
        raise ValueError(f"Invalid or non-existent directory: {startpath}")
    
    # Validate output file path
    output_path = Path(output_file)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create output directory: {str(e)}")

    # Use a lock for thread-safe list operations
    contents_lock = threading.Lock()
    contents: List[str] = []
    
    # Optimize number of workers based on CPU count
    num_workers = max(1, min(os.cpu_count() * 2, 32))  # Cap at 32 to prevent resource exhaustion
    
    logger.info(f"Starting directory scan with {num_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_file = {}
        for root, dirs, files in os.walk(startpath, topdown=True):
            # Log directories being scanned
            logger.debug(f"Scanning directory: {root}")
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            logger.debug(f"Directories after filtering: {dirs}")
            for file in files:
                future_to_file[executor.submit(process_file, root, file, ignore_dirs, ignore_extensions)] = file
        
        for future in concurrent.futures.as_completed(future_to_file):
            try:
                file_content = future.result()
                if file_content:
                    with contents_lock:
                        contents.extend(file_content)
                        logger.debug(f"Added content from file, current content length: {len(contents)}")
            except Exception as e:
                logger.error(f"Error processing future: {str(e)}")

    # Log contents before writing
    logger.debug(f"Total content lines to write: {len(contents)}")
    
    # Write results to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as out:
            out.writelines(contents)
        logger.info(f"Successfully wrote contents to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to output file: {str(e)}")
        raise

def main():
    """Main function to execute the directory contents builder."""
    code_repository_path = 'C:\\Users\\zimme\\OneDrive\\Documents\\GitHub\\flask-template-repo'
    output_file = 'output_main.txt'
    
    # Separate directory names and file extensions
    ignore_dirs = {
        'env', 'images', 'fonts', 'docs', '__pycache__', 'instance', 
        'tests', 'migrations', 'flask_stripe', '.git', 'fullcalendar',
    }
    ignore_extensions = {
        '.txt', '.css', '.gitattributes', '.md', '.pyc'
    }
    
    try:
        build_directory_contents(code_repository_path, output_file, ignore_dirs, ignore_extensions)
        print(f"Directory contents have been written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to build directory contents: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()