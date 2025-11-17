f'This script requires python version 3.6 or higher.'
import os
import sys
from pathlib import Path
import time
import json
import argparse
import subprocess
import shutil

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def error(msg):
    """Prints an error message and exits."""
    print(f'{Colors.RED}ERROR: {msg}{Colors.RESET}')
    sys.exit(1)

def log_info(msg):
    """Prints an info message."""
    print(f'{Colors.BLUE}INFO: {msg}{Colors.RESET}')

def log_warning(msg):
    """Prints a warning message."""
    print(f'{Colors.YELLOW}WARNING: {msg}{Colors.RESET}')
    
def load_config(config_path):
    """Loads the JSON configuration file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        error(f"Configuration file not found at '{config_path}'")
    except json.JSONDecodeError:
        error(f"Invalid JSON in configuration file '{config_path}'")

def construct_command(config, watch_folder, output_folder):
    """Constructs the command to run the encoder script."""
    if 'encoder_script_path' not in config:
        error("Config file must contain 'encoder_script_path' pointing to 'encode_dvmezz_to_dv7.py'")

    script_path = Path(config.pop('encoder_script_path'))
    command = [f'"{Path(sys.executable)}"', '-u']
    command.append(f'"{script_path}"')

    input_mov = Path(watch_folder) / 'DolbyMaster.mov'
    input_xml = Path(watch_folder) / 'DolbyMetadata.xml'

    # Add arguments from config file
    for key, value in config.items():
        # Quote paths to be safe with downstream tools like ffmpeg
        if isinstance(value, str) and ('\\' in value or '/' in value):
            # A simple check for path-like strings
            if Path(value).exists() or 'temp' in value:
                 value = f'"{value}"'

        if value is not None:
            command.append(f'--{key}')
            command.append(str(value))

    # Add specific input and output files
    command.extend(['--input', f'"{input_mov}"'])
    command.extend(['--input-metadata', f'"{input_xml}"'])

    base_name = Path(watch_folder).name
    output_bl = Path(output_folder) / f'{base_name}_bl.h265'
    output_el = Path(output_folder) / f'{base_name}_el.h265'
    
    command.extend(['--output-bl', f'"{output_bl}"'])
    command.extend(['--output-el', f'"{output_el}"'])

    return command

def run_encoding(command):
    """Runs the encoding command."""
    # On Windows, Popen with a list can fail with quoted paths, so we join and pass as a string.
    command_str = ' '.join(command)
    log_info(f"Running command: {command_str}")
    try:
        # Using shell=True because we have manually quoted the arguments.
        # We use text=False to read bytes and handle decoding manually for real-time output.
        process = subprocess.Popen(command_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        
        # Buffer to assemble lines from the subprocess output
        line_buffer = b''
        for chunk in iter(lambda: process.stdout.read(1), b''):
            line_buffer += chunk
            if b'\n' in line_buffer:
                line = line_buffer.split(b'\n')[0]
                line_buffer = line_buffer[len(line)+1:]
                
                line_str = line.decode(sys.stdout.encoding or 'utf-8', errors='replace').rstrip()
                
                # Colorize based on content, then print
                lower_line = line_str.lower()
                if 'error' in lower_line:
                    print(f'{Colors.RED}{line_str}{Colors.RESET}')
                elif 'warning' in lower_line:
                    print(f'{Colors.YELLOW}{line_str}{Colors.RESET}')
                else:
                    print(line_str) # Print original line if no keywords match

        process.wait() # Wait for the subprocess to finish
        if process.returncode != 0:
            log_warning(f"Encoding process failed with return code {process.returncode}.")
            return False
        else:
            print(f'{Colors.GREEN}INFO: Encoding process completed successfully.{Colors.RESET}')
            return True
    except FileNotFoundError:
        error(f"Could not execute command. Make sure '{command[0]}' is correct.")
        return False
    except Exception as e:
        error(f"An unexpected error occurred while running the encoder: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Watch a folder and run Dolby Vision profile 7 encoding.')
    parser.add_argument('--watch-folder', required=True, help='Folder to watch for DolbyMaster.mov and DolbyMetadata.xml.')
    parser.add_argument('--output-folder', required=True, help='Folder to save encoded files.')
    parser.add_argument('--processed-folder', required=True, help='Folder to move source files to after successful encoding.')
    parser.add_argument('--config', required=True, help='Path to the JSON config file for encoding.')
    parser.add_argument('--polling-interval', type=int, default=60, help='Interval in seconds to check the folder (default: 60).')
    args = parser.parse_args()

    watch_path = Path(args.watch_folder)
    output_path = Path(args.output_folder)
    processed_path = Path(args.processed_folder)

    if not watch_path.is_dir():
        error(f"Watch folder '{watch_path}' does not exist or is not a directory.")

    if not output_path.is_dir():
        log_info(f"Output folder '{output_path}' does not exist. Creating it.")
        output_path.mkdir(parents=True, exist_ok=True)

    if not processed_path.is_dir():
        log_info(f"Processed files folder '{processed_path}' does not exist. Creating it.")
        processed_path.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config)

    log_info(f"Watching folder: {watch_path}")
    log_info(f"Polling every {args.polling_interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            input_mov = watch_path / 'DolbyMaster.mov'
            input_xml = watch_path / 'DolbyMetadata.xml'

            if input_mov.exists() and input_xml.exists():
                log_info("Found DolbyMaster.mov and DolbyMetadata.xml. Starting encoding process.")
                
                command = construct_command(config, str(watch_path), str(output_path))
                
                if run_encoding(command):
                    # Move processed files to the specified processed folder
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    
                    try:
                        shutil.move(str(input_mov), str(processed_path / f'DolbyMaster_{timestamp}.mov'))
                        shutil.move(str(input_xml), str(processed_path / f'DolbyMetadata_{timestamp}.xml'))
                        log_info("Moved source files to 'processed' directory.")
                    except Exception as e:
                        error(f"Failed to move processed files: {e}")

                log_info(f"Waiting for new files. Checking again in {args.polling_interval} seconds.")
            
            time.sleep(args.polling_interval)

    except KeyboardInterrupt:
        log_info("\nWatcher stopped by user.")
        sys.exit(0)

if __name__ == '__main__':
    main()