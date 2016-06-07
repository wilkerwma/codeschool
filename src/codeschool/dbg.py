def console():
    """Starts an interactive IPython console"""

    import sys
    import builtins
    from IPython.terminal.embed import (load_default_config,
                                        InteractiveShell, InteractiveShellEmbed)

    header = 'Django debug console'
    config = load_default_config()
    config.InteractiveShellEmbed = config.TerminalInteractiveShell

    # save ps1/ps2 if defined
    ps1 = None
    ps2 = None
    try:
        ps1 = sys.ps1
        ps2 = sys.ps2
    except AttributeError:
        pass

    # save previous instance
    saved_shell_instance = InteractiveShell._instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()

    # Starts shell
    retvalue = None

    def exit(value=None):
        nonlocal retvalue
        retvalue = value

    try:
        builtins.exit = exit
        shell = InteractiveShellEmbed.instance(config=config)
        shell(header=header, stack_depth=2, compile_flags=None)
        InteractiveShellEmbed.clear_instance()
    finally:
        pass

    # restore previous instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()
        for subclass in cls._walk_mro():
            subclass._instance = saved_shell_instance
    if ps1 is not None:
        sys.ps1 = ps1
        sys.ps2 = ps2

    return retvalue
