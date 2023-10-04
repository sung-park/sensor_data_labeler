def log_method_call(func):
    def wrapper(*args, **kwargs):
        class_name = args[0].__class__.__name__
        method_name = func.__name__
        print(f"{class_name}.{method_name}...")
        result = func(*args, **kwargs)
        return result

    return wrapper
