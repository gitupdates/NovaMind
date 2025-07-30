"""Interactive helper for executing and improving Python snippets."""

import io
import sys
import logging
try:
    import autopep8
except ImportError:  # pragma: no cover - optional dependency
    autopep8 = None
    logging.warning("autopep8 is not installed. Formatting suggestions will be skipped.")
import ast
from typing import Dict, Any, List

# Configure logging to show information messages.
# This helps in debugging the assistant's own operations.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def interpret_and_execute_code(code_string: str) -> Dict[str, Any]:
    """
    Attempts to interpret and execute the given Python code string.
    Captures stdout and stderr during execution.

    This function demonstrates the 'execution' and initial 'interpretation'
    of Python code. It's crucial to note that using `exec()` with untrusted
    input can be a security risk. For this demonstration, it's used
    to show code execution and error capture.

    Args:
        code_string (str): The Python code to execute.

    Returns:
        Dict[str, Any]: A dictionary containing execution status, captured output,
                        error details, and error type/message if an error occurred.
    """
    # Redirect stdout and stderr to capture output and errors
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error

    result = {
        "status": "success",
        "output": "",
        "error": "",
        "error_type": None,
        "error_message": ""
    }

    try:
        # Execute the code. Using empty global/local dictionaries for `exec`
        # helps to isolate the execution environment and prevent unintended
        # side effects or access to the script's own variables.
        exec(code_string, {}, {})
        result["output"] = redirected_output.getvalue()
    except SyntaxError as e:
        # Catch specific SyntaxError for clearer feedback
        result["status"] = "syntax_error"
        result["error"] = redirected_error.getvalue()
        result["error_type"] = "SyntaxError"
        result["error_message"] = str(e)
        logging.error(f"Syntax Error: {e}")
    except Exception as e:
        # Catch any other runtime exceptions
        result["status"] = "runtime_error"
        result["error"] = redirected_error.getvalue()
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)
        logging.error(f"Runtime Error ({type(e).__name__}): {e}")
    finally:
        # Restore original stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        # Ensure any stderr output is captured even if no specific exception was caught
        if not result["error"] and redirected_error.getvalue():
            result["error"] = redirected_error.getvalue()
    return result

def error_correct_code_suggestion(execution_result: Dict[str, Any]) -> str:
    """
    Provides a basic error correction suggestion based on the execution result.
    This function demonstrates a simplified 'error correction' capability by
    offering common solutions for identified error types, drawing from the
    knowledge about Python's error handling.

    Args:
        execution_result (Dict[str, Any]): The result dictionary from `interpret_and_execute_code`.

    Returns:
        str: A human-readable suggestion for error correction.
    """
    if execution_result["status"] == "success":
        return "No errors detected. Code executed successfully."

    error_type = execution_result["error_type"]
    error_message = execution_result["error_message"]

    suggestion = f"Error Type: **{error_type}**\nError Message: `{error_message}`\n\n"

    # Provide specific suggestions based on common Python error types
    if error_type == "SyntaxError":
        suggestion += "Suggestion: Check for typos, missing colons, incorrect indentation, or unclosed parentheses/brackets/quotes. Pay attention to the line indicated in the error message."
    elif error_type == "NameError":
        suggestion += "Suggestion: A variable or function was used before it was defined, or it's misspelled. Ensure all names are correctly spelled and in scope. Remember Python is case-sensitive!"
    elif error_type == "TypeError":
        suggestion += "Suggestion: An operation was attempted on an incompatible data type (e.g., trying to add a string to an integer). Check the types of your variables before operations. Consider using type hints (`def func(arg: int) -> str:`) for clarity."
    elif error_type == "IndentationError":
        suggestion += "Suggestion: Python relies heavily on consistent indentation (usually 4 spaces per level). Ensure your code blocks (e.g., after `if`, `for`, `def`, `class`) have correct and uniform indentation."
    elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
        suggestion += "Suggestion: A required module or library is not found. Ensure it is installed in your environment (e.g., `pip install <module_name>`). If using a virtual environment, make sure it's activated."
    elif error_type == "ZeroDivisionError":
        suggestion += "Suggestion: You attempted to divide by zero. Add a check (e.g., an `if` statement) to ensure the divisor is not zero before performing division."
    elif error_type == "KeyError":
        suggestion += "Suggestion: You tried to access a dictionary key that does not exist. Double-check the key's spelling or use `dict.get()` with a default value."
    elif error_type == "IndexError":
        suggestion += "Suggestion: You tried to access an index that is out of the bounds of a list or other sequence. Ensure the index is within the valid range (0 to length-1)."
    else:
        suggestion += "Suggestion: This is a general runtime error. Review the traceback carefully to understand the sequence of calls leading to the error. Consider adding `print()` statements or using a debugger to inspect variable states. Implement more specific `try-except` blocks for anticipated errors."

    suggestion += "\n\nFor more in-depth information on specific errors, refer to the official Python Language Reference: [https://docs.python.org/3/reference/index.html](https://docs.python.org/3/reference/index.html)"
    return suggestion

def improve_code_suggestion(code_string: str) -> Dict[str, str]:
    """
    Provides suggestions for improving Python code based on common best practices
    from the knowledge corpus. This function demonstrates a simplified 'code improvement'
    capability, including automated formatting and conceptual suggestions.

    Args:
        code_string (str): The Python code to analyze for improvements.

    Returns:
        Dict[str, str]: A dictionary of improvement suggestions.
    """
    improvements = {}

    # 1. Automated Formatting (PEP 8 compliance)
    if autopep8 is not None:
        try:
            formatted_code = autopep8.fix_code(code_string)
            if formatted_code != code_string:
                improvements["formatted_code"] = formatted_code
                improvements["formatting_suggestion"] = (
                    "Code has been automatically formatted for **PEP 8 compliance** using `autopep8`. Consistent formatting improves readability."
                )
            else:
                improvements["formatting_suggestion"] = (
                    "Code already appears to be PEP 8 compliant (no changes by `autopep8`)."
                )
        except Exception as e:
            improvements["formatting_suggestion"] = f"Could not apply automatic formatting: {e}"
            logging.warning(f"Autopep8 failed: {e}")
    else:
        improvements["formatting_suggestion"] = (
            "autopep8 is not installed, so formatting suggestions are skipped."
        )

    # Use AST (Abstract Syntax Tree) for more structural analysis
    try:
        tree = ast.parse(code_string)

        # 2. Docstring/Type Hinting Suggestion
        # Check for functions without docstrings or type hints
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for docstring
                if not ast.get_docstring(node):
                    improvements["docstring_suggestion"] = improvements.get("docstring_suggestion", "") + \
                        f"Consider adding a **docstring** to function `{node.name}` to explain its purpose, arguments, and return values (e.g., using Google or NumPy style)."

                # Check for type hints (simplified: just checking for any annotations)
                if not node.returns and not any(arg.annotation for arg in node.args.args):
                    improvements["type_hint_suggestion"] = improvements.get("type_hint_suggestion", "") + \
                        f"Add **type hints** to parameters and the return value of function `{node.name}` for better readability and static analysis."
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    improvements["class_docstring_suggestion"] = improvements.get("class_docstring_suggestion", "") + \
                        f"Consider adding a **docstring** to class `{node.name}` to explain its purpose."

        # 3. Basic Refactoring Suggestion (e.g., list comprehension for simple loops)
        # This is a very simple heuristic and won't catch all cases.
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Call):
                    if isinstance(node.body[0].value.func, ast.Attribute) and node.body[0].value.func.attr == 'append':
                        improvements["refactoring_suggestion"] = improvements.get("refactoring_suggestion", "") + \
                            "If you are building a list using a `for` loop and `.append()`, consider using a more concise **list comprehension** for better readability and often performance."
                        break # Only suggest once per code block

        # 4. File Handling Suggestion (using 'with' statement)
        if "open(" in code_string and ".close()" in code_string and "with open" not in code_string:
             improvements["file_handling_suggestion"] = "When working with files, always use a `with open(...)` statement. It ensures the file is properly closed even if errors occur, preventing resource leaks."

    except SyntaxError:
        improvements["analysis_warning"] = "Could not perform deeper code analysis due to syntax errors. Please fix syntax first."
    except Exception as e:
        improvements["analysis_warning"] = f"An error occurred during code analysis: {e}"
        logging.warning(f"AST analysis failed: {e}")

    # 5. Dependency Management Reminder (always relevant)
    improvements["dependency_reminder"] = "Remember to manage your project dependencies using a `requirements.txt` file or a tool like `poetry` or `pipenv`. Always install dependencies in a **virtual environment** to avoid conflicts."

    # 6. General Best Practices Reminder (always relevant)
    improvements["general_best_practices"] = """
    **General Best Practices Reminders:**
    * **Modular Structure:** Break code into smaller, reusable functions and classes (**DRY Principle**).
    * **Descriptive Naming:** Use clear and meaningful names for all identifiers.
    * **Error Handling:** Use `try-except` blocks for graceful error management.
    * **Testing:** Write unit tests (`pytest`, `unittest`) and aim for good test coverage (`coverage.py`).
    * **Security:** Regularly scan for vulnerabilities (`bandit`, `safety`).
    * **Performance:** Profile your code (`cProfile`) and optimize algorithms/data structures.
    * **Documentation:** Maintain clear **docstrings** and **READMEs** for your projects.
    """

    return improvements

def main() -> None:
    """
    Main function to demonstrate Python code interpretation, error correction, and improvement.
    This acts as a basic interactive console for the AI's capabilities.
    """
    print("Welcome to the Python Code Assistant!")
    print("This tool can interpret, error-correct, and suggest improvements for your Python code.")
    print("---")
    print("To use, enter your Python code. For multi-line input, press Enter on an empty line to submit.")
    print("Type 'quit()' to exit the assistant.")
    print("---")

    while True:
        print("\nEnter your Python code:")
        code_lines = []
        while True:
            try:
                line = input()
                if not line: # Empty line signals end of input
                    break
                code_lines.append(line)
            except EOFError: # Handle Ctrl+D (Unix) or Ctrl+Z (Windows)
                print("\nEOF detected. Exiting Python Code Assistant. Goodbye!")
                return

        user_code = "\n".join(code_lines)

        if user_code.strip().lower() == "quit()":
            print("Exiting Python Code Assistant. Goodbye!")
            break

        if not user_code.strip():
            print("No code entered. Please try again.")
            continue

        print("\n--- Interpreting and Executing Code ---")
        execution_result = interpret_and_execute_code(user_code)

        print(f"**Execution Status:** {execution_result['status'].replace('_', ' ').title()}")
        if execution_result["output"]:
            print("\n--- Captured Output (stdout) ---")
            print(execution_result["output"].strip())
        if execution_result["error"]:
            print("\n--- Captured Error (stderr) ---")
            print(execution_result["error"].strip())

        print("\n--- Error Correction Suggestions ---")
        print(error_correct_code_suggestion(execution_result))

        print("\n--- Code Improvement Suggestions ---")
        improvement_suggestions = improve_code_suggestion(user_code)

        # Display formatted code if available
        if "formatted_code" in improvement_suggestions:
            print("\n**Suggested Formatted Code:**")
            print("```python")
            print(improvement_suggestions["formatted_code"])
            print("```")
            del improvement_suggestions["formatted_code"] # Remove to avoid printing it again in the list

        # Display other improvement suggestions
        for key, value in improvement_suggestions.items():
            print(f"- **{key.replace('_', ' ').title()}:** {value}")

        print("\n--- End of Analysis ---")

if __name__ == "__main__":
    main()
