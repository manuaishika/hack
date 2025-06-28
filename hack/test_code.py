"""
test_code.py
sample code to test the enhanced analyzer with various function types
"""

import threading
import asyncio
import time

def used_function():
    """this function is actually used"""
    print("hello from used function")
    return "used"

def unused_function():
    """this function is never called - dead code"""
    print("this will never be printed")
    return "unused"

def complex_unused_function():
    """complex unused function with loops and conditionals"""
    result = 0
    for i in range(100):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    # nested loops for higher complexity
    for i in range(10):
        for j in range(10):
            result += i * j
    
    return result

async def async_function():
    """async function that might be hard to detect statically"""
    await asyncio.sleep(0.1)
    return "async result"

def threaded_function():
    """function that uses threading"""
    def worker():
        time.sleep(0.1)
        print("worker thread completed")
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    return "threaded result"

def main():
    """main function that calls some functions"""
    used_function()
    
    # async function call
    asyncio.run(async_function())
    
    # threaded function call
    threaded_function()

if __name__ == "__main__":
    main() 