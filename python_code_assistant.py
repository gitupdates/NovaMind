#!/usr/bin/env python3

import io
import sys
import logging
import argparse
try:
    import autopep8
    AUTOPEP8_AVAILABLE = True
except ImportError:  # Graceful fallback if autopep8 is missing
    AUTOPEP8_AVAILABLE = False
    autopep8 = None
import ast
from typing import Dict, Any, List

# Configure logging to show information messages.
# This helps in debugging the assistant's own operations.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# This list contains comprehensive Python knowledge,
# ready to be conceptually leveraged by the AI chatbot. It covers
# foundational concepts, syntax, style, error handling,
# testing, security, performance, documentation, tooling,
# and packaging, enabling the AI to perfect its coding skills.
# In a real-world AI system, this knowledge would be part of the
# model's training data or dynamically retrieved based on context.
python_knowledge_corpus: List[Dict[str, str]] = [
    {
        "id": "foundations_modular_dry_naming",
        "content": """
        ## Foundations: Writing Functional Code
        Start with clean design principles:

        * **Modular Structure:** Break code into functions and classes for reuse and clarity.
        * **DRY Principle (“Don’t Repeat Yourself”):** Eliminate duplication; abstract logic into reusable components.
        * **Descriptive Naming:** Use clear, meaningful names for variables, functions, and modules.
        """
    },
    {
        "id": "core_syntax_keywords",
        "content": """
        ## Core Language Components: Syntax & Keywords
        Python's fundamental building blocks: if, for, while, class, def, return, yield, global, nonlocal, try, except, finally, raise, import, from, as, lambda, pass, break, continue.
        """
    },
    {
        "id": "core_built_in_data_types",
        "content": """
        ## Core Language Components: Built-in Data Types
        * **Numeric:** int, float, complex
        * **Sequence:** list, tuple, range
        * **Text:** str
        * **Set types:** set, frozenset
        * **Mappings:** dict
        * **Boolean:** bool
        * **Binary:** bytes, bytearray
        """
    },
    {
        "id": "core_operators",
        "content": """
        ## Core Language Components: Operators
        * **Arithmetic:** (+, -, *, /, //, %, **)
        * **Logical:** (and, or, not)
        * **Comparison:** (==, !=, >, <, >=, <=)
        * **Assignment:** (=, +=, etc.)
        * **Identity:** (is, is not)
        * **Membership:** (in, not in)
        """
    },
    {
        "id": "core_control_flow",
        "content": """
        ## Core Language Components: Control Flow
        if, elif, else, for loops, while loops, break, continue, pass.
        Best practices for looping (e.g., using enumerate, zip).
        """
    },
    {
        "id": "core_exception_handling",
        "content": """
        ## Core Language Components: Exception Handling
        try, except, finally, raise.
        Specific exception types (ValueError, TypeError, FileNotFoundError, IndexError, KeyError, ZeroDivisionError).
        Custom exceptions.
        Best practices for handling exceptions (e.g., catching specific exceptions, logging, re-raising).
        """
    },
    {
        "id": "core_functions",
        "content": """
        ## Core Language Components: Functions
        Definition (def), lambda expressions, parameters, arguments (positional, keyword, default, *args, **kwargs), return values, yield (for generators), global, nonlocal.
        **Docstrings (PEP 257)** and **type hints (PEP 484)**.
        Function purity and side effects.
        """
    },
    {
        "id": "core_classes_oop",
        "content": """
        ## Core Language Components: Classes & OOP
        class definition, objects, inheritance, super(), **dunder methods** (__init__, __str__, __len__, __call__, etc.), polymorphism, encapsulation, abstraction.
        Instance vs. class variables, @classmethod, @staticmethod, properties.
        Design patterns (e.g., Singleton, Factory, Strategy) in Python.
        """
    },
    {
        "id": "core_modules_imports",
        "content": """
        ## Core Language Components: Modules & Imports
        import, from ... import ..., as keyword, __init__.py, package structure.
        Structuring larger projects.
        """
    },
    {
        "id": "standard_library_file_io",
        "content": """
        ## Standard Library Modules: File I/O
        **os**, **io**, **shutil**, **pathlib**.
        """
    },
    {
        "id": "standard_library_math_numbers",
        "content": """
        ## Standard Library Modules: Math & Numbers
        **math**, **decimal**, **fractions**, **random**.
        """
    },
    {
        "id": "standard_library_dates_times",
        "content": """
        ## Standard Library Modules: Dates & Times
        **datetime**, **time**, **calendar**.
        """
    },
    {
        "id": "standard_library_networking",
        "content": """
        ## Standard Library Modules: Networking
        **socket**, **http.client**, **urllib**.
        """
    },
    {
        "id": "standard_library_data_handling",
        "content": """
        ## Standard Library Modules: Data Handling
        **json**, **csv**, **xml.etree**, **pickle**, **sqlite3**.
        """
    },
    {
        "id": "standard_library_concurrency",
        "content": """
        ## Standard Library Modules: Concurrency
        **threading**, **multiprocessing**, **asyncio**.
        """
    },
    {
        "id": "standard_library_testing",
        "content": """
        ## Standard Library Modules: Testing
        **unittest**, **doctest**.
        """
    },
    {
        "id": "syntax_style_pep8",
        "content": """
        ## Syntax & Style: Ensuring Consistency - PEP 8 Compliance
        Use spaces around operators, indentation (4 spaces), line length (<79 chars).
        Tools: **black**, **autopep8**, **isort** for formatting and sorting imports.
        """
    },
    {
        "id": "syntax_style_type_hinting",
        "content": """
        ## Syntax & Style: Ensuring Consistency - Type Hinting
        Helps readability and static analysis: def add(x: int, y: int) -> int.
        Tools: **mypy**, **pytype**.
        """
    },
    {
        "id": "error_prevention_validation",
        "content": """
        ## Error Prevention & Handling - Validation
        Validate inputs using assert statements or libraries like **pydantic**.
        """
    },
    {
        "id": "error_prevention_logging",
        "content": """
        ## Error Prevention & Handling - Logging
        Use the **logging** module to record errors, warnings, and debug info.
        """
    },
    {
        "id": "testing_unit_frameworks",
        "content": """
        ## Testing & Code Quality - Unit Testing
        Frameworks: **pytest**, **unittest**, **nose2**.
        Best practices for writing effective unit tests (e.g., independent tests, fast execution, descriptive names, testing edge cases).
        """
    },
    {
        "id": "testing_coverage",
        "content": """
        ## Testing & Code Quality - Test Coverage
        Use **coverage.py** to evaluate how much of your code is tested.
        """
    },
    {
        "id": "testing_ci_cd",
        "content": """
        ## Testing & Code Quality - CI/CD Integration
        Automate tests on every change via **GitHub Actions**, **GitLab CI**, etc.
        """
    },
    {
        "id": "security_static_analysis",
        "content": """
        ## Security & Auditing - Static Analysis
        Scan for vulnerabilities using tools like **bandit**, **safety**, or **pip-audit**.
        Linters & Type Checkers: **pylint**, **flake8**, **black**, **mypy**.
        pyflakes for unused variables.
        """
    },
    {
        "id": "security_dependency_checks",
        "content": """
        ## Security & Auditing - Dependency Checks
        Keep packages up to date; review **CVEs** (Common Vulnerabilities and Exposures) tied to dependencies.
        """
    },
    {
        "id": "performance_profiling",
        "content": """
        ## Performance & Optimization - Profiling
        Use **cProfile**, **line_profiler** to find bottlenecks.
        """
    },
    {
        "id": "performance_memory_efficiency",
        "content": """
        ## Performance & Optimization - Memory Efficiency
        Use **generators** where appropriate, avoid unnecessary data copies.
        """
    },
    {
        "id": "performance_algorithmic_improvements",
        "content": """
        ## Performance & Optimization - Algorithmic Improvements
        Choosing more efficient algorithms and data structures.
        """
    },
    {
        "id": "performance_vectorization",
        "content": """
        ## Performance & Optimization - Vectorization
        Leveraging optimized C implementations for numerical operations (**NumPy/Pandas**).
        """
    },
    {
        "id": "performance_concurrency_parallelism",
        "content": """
        ## Performance & Optimization - Concurrency and Parallelism
        * threading (for I/O bound tasks).
        * multiprocessing (for CPU bound tasks, bypassing GIL).
        * asyncio (for asynchronous I/O).
        """
    },
    {
        "id": "documentation_docstrings",
        "content": """
        ## Documentation & Comments - Docstrings
        Add to functions/classes using **NumPy** or **Google style**.
        """
    },
    {
        "id": "documentation_inline_comments",
        "content": """
        ## Documentation & Comments - Inline Comments
        Explain non-obvious logic or domain-specific decisions.
        """
    },
    {
        "id": "documentation_readme_api_docs",
        "content": """
        ## Documentation & Comments - README & API Docs
        Use **MkDocs**, **Sphinx**, or **pdoc** for full documentation sets.
        """
    },
    {
        "id": "tooling_linters",
        "content": """
        ## Tooling for Project Health - Linters
        **flake8**, **pylint**, **ruff** to catch code smells and enforce style.
        """
    },
    {
        "id": "tooling_virtual_environment",
        "content": """
        ## Tooling for Project Health - Virtual Environment
        Use **venv** or **conda** to isolate dependencies.
        """
    },
    {
        "id": "tooling_version_control",
        "content": """
        ## Tooling for Project Health - Version Control
        **Git** with branching strategies, semantic commit messages.
        """
    },
    {
        "id": "packaging_tools",
        "content": """
        ## Packaging & Publishing - Packaging Tools
        **setuptools**, **poetry**, **flit** to build installable Python packages.
        """
    },
    {
        "id": "packaging_pyproject_toml",
        "content": """
        ## Packaging & Publishing - pyproject.toml
        Modern way to define project metadata and build system.
        [project] section (name, version, description, dependencies).
        [build-system] (e.g., setuptools, hatchling).
        """
    },
    {
        "id": "packaging_building_distribution",
        "content": """
        ## Packaging & Publishing - Building Distribution Packages
        Creating source distributions (.tar.gz) and wheel distributions (.whl).
        Using python -m build.
        """
    },
    {
        "id": "packaging_pypi_twine",
        "content": """
        ## Packaging & Publishing - Distributing Platforms (PyPI)
        **PyPI** (Python Package Index) using **twine** to upload packages.
        """
    },
    {
        "id": "packaging_github",
        "content": """
        ## Packaging & Publishing - Distributing Platforms (GitHub)
        **GitHub** for source control and collaboration.
        """
    },
    {
        "id": "packaging_ci_cd",
        "content": """
        ## Packaging & Publishing - Continuous Integration/Continuous Deployment (CI/CD)
        Automating testing, building, and publishing workflows (e.g., **GitHub Actions**, **GitLab CI**).
        """
    },
    {
        "id": "dependency_package_managers",
        "content": """
        ## Dependency Management and Installation - Package Managers
        * **pip**: The standard package installer for Python.
            * Basic usage: pip install <package_name>.
            * Installing from requirements.txt: pip install -r requirements.txt.
            * Upgrading packages: pip install --upgrade <package_name>.
            * Uninstalling packages: pip uninstall <package_name>.
        * **conda**: Cross-platform package and environment manager (especially for data science).
            * Basic usage: conda install <package_name>.
            * Environment management: conda create -n myenv python=3.9, conda activate myenv.
        * **poetry**: A dependency management and packaging tool.
            * Installation: poetry install.
            * Adding dependencies: poetry add <package_name>.
        * **pipenv**: Combines pip and virtualenv into a single tool.
        """
    },
    {
        "id": "dependency_virtual_environments",
        "content": """
        ## Dependency Management and Installation - Virtual Environments
        **Crucial for isolating project dependencies.**
        Instructions on creating and activating venv or conda environments.
        Why to always install project-specific libraries within a virtual environment.
        """
    },
    {
        "id": "dependency_checking_availability",
        "content": """
        ## Dependency Management and Installation - Checking for Module Availability
        Programmatic checks using try-except ImportError.
        Command-line checks (e.g., pip show <package_name>).
        """
    },
    {
        "id": "dependency_installation_instructions",
        "content": """
        ## Dependency Management and Installation - Including Installation Instructions in Code/Documentation
        Best practice: Always include a requirements.txt file (or pyproject.toml with dependencies) in your project.
        Provide clear, step-by-step instructions for users to set up a virtual environment and install dependencies before running any code.
        """
    }
]


def interpret_and_execute_code(code_string: str) -> Dict[str, Any]:
    """
    Attempts to interpret and execute the given Python code string.
    Captures stdout and stderr during execution.

    This function demonstrates the 'execution' and initial 'interpretation'
    of Python code. It's crucial to note that using exec() with untrusted
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
        # Execute the code. Using empty global/local dictionaries for exec
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
        execution_result (Dict[str, Any]): The result dictionary from interpret_and_execute_code.

    Returns:
        str: A human-readable suggestion for error correction.
    """
    if execution_result["status"] == "success":
        return "No errors detected. Code executed successfully."

    error_type = execution_result["error_type"]
    error_message = execution_result["error_message"]

    suggestion = f"Error Type: **{error_type}**\nError Message: {error_message}\n\n"

    # Provide specific suggestions based on common Python error types
    if error_type == "SyntaxError":
        suggestion += "Suggestion: Check for typos, missing colons, incorrect indentation, or unclosed parentheses/brackets/quotes. Pay attention to the line indicated in the error message."
    elif error_type == "NameError":
        suggestion += "Suggestion: A variable or function was used before it was defined, or it's misspelled. Ensure all names are correctly spelled and in scope. Remember Python is case-sensitive!"
    elif error_type == "TypeError":
        suggestion += "Suggestion: An operation was attempted on an incompatible data type (e.g., trying to add a string to an integer). Check the types of your variables before operations. Consider using type hints (def func(arg: int) -> str:) for clarity."
    elif error_type == "AttributeError":
        suggestion += "Suggestion: An attribute or method is missing on an object. Double-check the object's type and available attributes (dir(obj))."
    elif error_type == "ValueError":
        suggestion += "Suggestion: A function received a value of correct type but invalid content. Validate inputs before using them."
    elif error_type == "FileNotFoundError":
        suggestion += "Suggestion: The file path does not exist. Check your working directory and ensure the path is correct."
    elif error_type == "RecursionError":
        suggestion += "Suggestion: Maximum recursion depth exceeded. Convert deep recursion to iteration or increase the limit via sys.setrecursionlimit() with care."
    elif error_type == "MemoryError":
        suggestion += "Suggestion: The operation ran out of memory. Process data in chunks, use generators, or optimize your algorithm."
    elif error_type == "OSError":
        suggestion += "Suggestion: An OS-level error occurred (permissions, missing resources, etc.). Inspect e.errno and e.strerror for more details."
    elif error_type == "IndentationError":
        suggestion += "Suggestion: Python relies heavily on consistent indentation (usually 4 spaces per level). Ensure your code blocks (e.g., after if, for, def, class) have correct and uniform indentation."
    elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
        suggestion += "Suggestion: A required module or library is not found. Ensure it is installed in your environment (e.g., pip install <module_name>). If using a virtual environment, make sure it's activated."
    elif error_type == "ZeroDivisionError":
        suggestion += "Suggestion: You attempted to divide by zero. Add a check (e.g., an if statement) to ensure the divisor is not zero before performing division."
    elif error_type == "KeyError":
        suggestion += "Suggestion: You tried to access a dictionary key that does not exist. Double-check the key's spelling or use dict.get() with a default value."
    elif error_type == "IndexError":
        suggestion += "Suggestion: You tried to access an index that is out of the bounds of a list or other sequence. Ensure the index is within the valid range (0 to length-1) and watch for negative indices."
    else:
        suggestion += "Suggestion: This is a general runtime error. Review the traceback carefully to understand the sequence of calls leading to the error. Consider adding print() statements or using a debugger to inspect variable states. Implement more specific try-except blocks for anticipated errors."

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
    if AUTOPEP8_AVAILABLE:
        try:
            # autopep8.fix_code applies PEP 8 formatting
            formatted_code = autopep8.fix_code(code_string)
            if formatted_code != code_string:
                improvements["formatted_code"] = formatted_code
                improvements["formatting_suggestion"] = "Code has been automatically formatted for **PEP 8 compliance** using autopep8. Consistent formatting improves readability."
            else:
                improvements[
                    "formatting_suggestion"] = "Code already appears to be PEP 8 compliant (no changes by autopep8)."
        except Exception as e:
            improvements[
                "formatting_suggestion"] = f"Could not apply automatic formatting: {e}"
            logging.warning(f"Autopep8 failed: {e}")
    else:
        improvements["formatting_suggestion"] = (
            "autopep8 is not installed. Install it for automatic PEP 8 formatting suggestions."
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
                        f"Consider adding a **docstring** to function {node.name} to explain its purpose, arguments, and return values (e.g., using Google or NumPy style)."

                # Check for type hints (simplified: just checking for any annotations)
                if not node.returns and not any(arg.annotation for arg in node.args.args):
                    improvements["type_hint_suggestion"] = improvements.get("type_hint_suggestion", "") + \
                        f"Add **type hints** to parameters and the return value of function {node.name} for better readability and static analysis."
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    improvements["class_docstring_suggestion"] = improvements.get("class_docstring_suggestion", "") + \
                        f"Consider adding a **docstring** to class {node.name} to explain its purpose."

        # 3. Basic Refactoring Suggestion (e.g., list comprehension for simple loops)
        # This is a very simple heuristic and won't catch all cases.
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Call):
                    if isinstance(node.body[0].value.func, ast.Attribute) and node.body[0].value.func.attr == 'append':
                        improvements["refactoring_suggestion"] = improvements.get("refactoring_suggestion", "") + \
                            "If you are building a list using a for loop and .append(), consider using a more concise **list comprehension** for better readability and often performance."
                        break  # Only suggest once per code block

        # 4. File Handling Suggestion (using 'with' statement)
        if "open(" in code_string and ".close()" in code_string and "with open" not in code_string:
            improvements["file_handling_suggestion"] = "When working with files, always use a with open(...) statement. It ensures the file is properly closed even if errors occur, preventing resource leaks."

    except SyntaxError:
        improvements["analysis_warning"] = "Could not perform deeper code analysis due to syntax errors. Please fix syntax first."
    except Exception as e:
        improvements["analysis_warning"] = f"An error occurred during code analysis: {e}"
        logging.warning(f"AST analysis failed: {e}")

    # 5. Dependency Management Reminder (always relevant)
    improvements["dependency_reminder"] = "Remember to manage your project dependencies using a requirements.txt file or a tool like poetry or pipenv. Always install dependencies in a **virtual environment** to avoid conflicts."

    # 6. General Best Practices Reminder (always relevant)
    improvements["general_best_practices"] = """
    **General Best Practices Reminders:**
    * **Modular Structure:** Break code into smaller, reusable functions and classes (**DRY Principle**).
    * **Descriptive Naming:** Use clear and meaningful names for all identifiers.
    * **Error Handling:** Use try-except blocks for graceful error management.
    * **Testing:** Write unit tests (pytest, unittest) and aim for good test coverage (coverage.py).
    * **Security:** Regularly scan for vulnerabilities (bandit, safety).
    * **Performance:** Profile your code (cProfile) and optimize algorithms/data structures.
    * **Documentation:** Maintain clear **docstrings** and **READMEs** for your projects.
    """

    return improvements


def main() -> None:
    """
    Main function to demonstrate Python code interpretation, error correction, and improvement.
    This acts as a basic interactive console for the AI's capabilities.
    """
    parser = argparse.ArgumentParser(
        description="Interactive Python Code Assistant")
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Run code from the specified file instead of starting the interactive console.",
    )
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
        except OSError as exc:
            print(f"Failed to read file: {exc}")
            return

        execution_result = interpret_and_execute_code(code)
        print(
            f"**Execution Status:** {execution_result['status'].replace('_', ' ').title()}")
        if execution_result["output"]:
            print("\n--- Captured Output (stdout) ---")
            print(execution_result["output"].strip())
        if execution_result["error"]:
            print("\n--- Captured Error (stderr) ---")
            print(execution_result["error"].strip())

        print("\n--- Error Correction Suggestions ---")
        print(error_correct_code_suggestion(execution_result))

        print("\n--- Code Improvement Suggestions ---")
        improvement_suggestions = improve_code_suggestion(code)
        if "formatted_code" in improvement_suggestions:
            print("\n**Suggested Formatted Code:**")
            print("```python")
            print(improvement_suggestions["formatted_code"])
            print("```")
            del improvement_suggestions["formatted_code"]
        for key, value in improvement_suggestions.items():
            print(f"- **{key.replace('_', ' ').title()}:** {value}")
        return

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
                if not line:  # Empty line signals end of input
                    break
                code_lines.append(line)
            except EOFError:  # Handle Ctrl+D (Unix) or Ctrl+Z (Windows)
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

        print(
            f"**Execution Status:** {execution_result['status'].replace('_', ' ').title()}")
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
            # Remove to avoid printing it again in the list
            del improvement_suggestions["formatted_code"]

        # Display other improvement suggestions
        for key, value in improvement_suggestions.items():
            print(f"- **{key.replace('_', ' ').title()}:** {value}")

        print("\n--- End of Analysis ---")


if __name__ == "__main__":
    main()
