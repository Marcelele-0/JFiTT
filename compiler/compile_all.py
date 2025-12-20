import os
import subprocess
import sys

def compile_all():
    # Define paths relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    compiler_script = os.path.join(base_dir, 'src', 'compiler.py')
    test_files_dir = os.path.join(base_dir, 'test_files')
    output_dir = os.path.join(base_dir, 'test_outputs')

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Get all .imp files
    if not os.path.exists(test_files_dir):
        print(f"Error: Test files directory not found at {test_files_dir}")
        return

    files = [f for f in os.listdir(test_files_dir) if f.endswith('.imp')]
    
    if not files:
        print("No .imp files found in test_files directory.")
        return

    print(f"Found {len(files)} test files. Starting compilation...")
    print(f"Compiler script: {compiler_script}")
    print(f"Output directory: {output_dir}")
    print("-" * 40)

    success_count = 0
    fail_count = 0

    for filename in files:
        input_path = os.path.join(test_files_dir, filename)
        # Use .mr extension for the machine code output
        output_filename = os.path.splitext(filename)[0] + '.mr'
        output_path = os.path.join(output_dir, output_filename)

        print(f"Compiling {filename} -> {output_filename}...", end=' ', flush=True)
        
        # Run the compiler script
        try:
            result = subprocess.run(
                [sys.executable, compiler_script, input_path, output_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("OK")
                success_count += 1
            else:
                print("FAILED")
                print(f"  Error output:\n{result.stderr}")
                print(f"  Standard output:\n{result.stdout}")
                fail_count += 1
                
        except Exception as e:
            print(f"ERROR")
            print(f"  Failed to run compiler: {e}")
            fail_count += 1

    print("-" * 40)
    print(f"Compilation finished.")
    print(f"Successful: {success_count}")
    print(f"Failed:     {fail_count}")

if __name__ == "__main__":
    compile_all()
