import os

def create_llm_context(project_path, output_file="llm_context.txt"):
    """
    Crawls a project directory and combines all relevant files into a single
    file for use as a Large Language Model (LLM) context.

    Args:
        project_path (str): The path to the root of the project directory.
        output_file (str): The name of the file to save the combined context.
    """
    # Common files and directories to exclude from the context
    excluded_items = {
        '.git',
        '__pycache__',
        '.gitignore',
        '.env',
        output_file
    }

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # os.walk recursively explores the directory structure
        for root, dirs, files in os.walk(project_path):
            # Exclude specified directories from traversal
            dirs[:] = [d for d in dirs if d not in excluded_items]

            for file_name in files:
                if file_name not in excluded_items:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, project_path)

                    try:
                        outfile.write(f"--- File: {relative_path} ---\n\n")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n\n")
                    except Exception as e:
                        outfile.write(f"*** Error reading file: {e} ***\n\n")

if __name__ == '__main__':
    # Get the directory where the script is being run
    project_directory = os.getcwd()
    output_filename = "combined_project_files.txt"

    print(f"Starting to combine files from: {project_directory}")
    create_llm_context(project_directory, output_filename)
    print(f"All relevant files have been combined into: {output_filename}")