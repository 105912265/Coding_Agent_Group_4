from tools.execution.code_executor import execute_code


code = """
numbers = [3, 8, 2, 15, 6]

print(max(numbers))

"""


result = execute_code(
    code=code,
    language="python"
)


print("Success:", result["success"])
print("Output:", result["stdout"])
print("Error:", result["stderr"])
print("Exit code:", result["exit_code"])