from agents import function_tool

@function_tool
def test_func(x: int) -> int:
    return x * 2

print("Attributes:", [a for a in dir(test_func) if not a.startswith('_')])
print("Has fn:", hasattr(test_func, 'fn'))
print("Has func:", hasattr(test_func, 'func'))
print("Has raw:", hasattr(test_func, 'raw'))
print("Has _fn:", hasattr(test_func, '_fn'))

# Try to call
try:
    result = test_func(5)
    print("Direct call result:", result)
except Exception as e:
    print("Direct call error:", e)

# Check if it's callable
print("Callable:", callable(test_func))
