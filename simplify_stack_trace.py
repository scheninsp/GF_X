import re

def simplify_stack_trace(input_file, output_file):
    """
    Reads a detailed stack trace from input_file, simplifies it, and writes the result to output_file.

    The simplification logic is as follows:
    1. For each line, extract the "ClassName:MethodName".
    2. For each line, extract the line number.
    3. Combine them into "ClassName:MethodName LineNumber".
    """
    output_lines = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
        return

    # Regex to find the full method signature like "Namespace.ClassName:MethodName("
    method_pattern = re.compile(r'([\w\.]+:\w+)\s*\(')
    # Regex to find line number either in "[123:..." or at ":-1"
    line_pattern = re.compile(r':\[(\d+)| at :(-?\d+)')

    for line in lines:
        method_match = method_pattern.search(line)
        line_match = line_pattern.search(line)

        if method_match:
            # Extract full signature, e.g., "Some.Namespace.ClassName:MethodName"
            full_method_signature = method_match.group(1)
            
            # Split into class and method parts
            class_path, method_name = full_method_signature.rsplit(':', 1)
            
            # Get just the class name from its full path
            class_name = class_path.split('.')[-1]
            
            simplified_method = f"{class_name}:{method_name}"

            line_number = "N/A"
            if line_match:
                # group(1) is for the `[ddd]` pattern, group(2) is for the `:ddd` pattern.
                line_number = line_match.group(1) or line_match.group(2)
            
            output_lines.append(f"{simplified_method} {line_number}")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"Successfully processed {input_file} and wrote to {output_file}")
    except IOError as e:
        print(f"Error writing to output file {output_file}: {e}")

if __name__ == "__main__":
    # Define the input and output filenames
    INPUT_FILENAME = 'gemini_task.txt'
    OUTPUT_FILENAME = 'out.txt'
    simplify_stack_trace(INPUT_FILENAME, OUTPUT_FILENAME)