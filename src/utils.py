def safe_print(*args):
    try:
        print(*args)
    except UnicodeEncodeError:
        string = ""
        for arg in args[:-1]:
            string += str(arg) + " "
        string += str(args[-1])
        print(string.encode("utf-8"))
