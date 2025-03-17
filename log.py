class log(object):
    def __print(level : int, message : str):
        colour = 0
        tag = ""
        match level:
            case 0: colour = 44; tag = " DBUG "
            case 1: colour = 42; tag = " INFO "
            case 2: colour = 43; tag = " WARN "
            case 3: colour = 41; tag = " FAIL "

#        print(f"\033[30;1;{colour}m{tag}\033[0m {message}")
        print(f"[ {tag} ] {message}", flush=True)

    def dbug(message : str): log.__print(0, message)
    def info(message : str): log.__print(1, message)
    def warn(message : str): log.__print(2, message)
    def fail(message : str): log.__print(3, message)

