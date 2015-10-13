import os
import contextlib
import pwd
import subprocess
from subprocess import CalledProcessError
from fs.tempfs import TempFS
from django.utils.html import escape as escape_html


@contextlib.contextmanager
def tempdir(path):
    '''Temporarely sets the working directory to the given working_dir.
    Restores the original working_dir after leaving the with block.
    '''

    old_path = os.getcwd()
    try:
        os.chdir(path)
        yield None
    finally:
        os.chdir(old_path)


class Message(object):

    '''Represents a message that can be rendered using different methods.'''

    def __init__(self, data, success=False):
        self.data = data
        self.success = success

    def render(self, method='string'):
        '''Render message as 'string' or 'html', depending on the chosen
        method'''

        if method == 'html':
            return self._render_html()
        elif method == 'string':
            return self._render_string()
        else:
            raise ValueError('invalid render method: %s' % method)

    def _reder_html(self):
        return escape_html(self.render_string())

    def _render_string(self):
        return str(self.data)

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.data)


class ErrorMessage(Message):

    def __init__(self, data):
        super().__init__(data, success=False)

    def _render_string(self):
        ex = self.data
        if isinstance(self.data, CalledProcessError):
            data = ex.output
            data += 'Error: exited with code %s' % ex.returncode
        else:
            data = '%s: %s' % (type(ex).__name__, ex)
        return data


class ExceptionMessage(Message):
    pass
    # def _render_html(self):
    #    pass


class Sandbox(object):

    '''
    Creates a generic sandbox environment that can be used to run arbitrary
    executables.

    The sandboxed job consists of three phases: preparation, build and
    execution.

        1) The first phase is used to insert files or set up any configuration
           options. This phase should always succeed irrespective of user
           input. Tipically it involves copying files and preparing the build
           environment.
        2) The second phase uses the user provided information and build or
           prepares an executable. This phase can throw syntax errors, but
           should not be vunerable to malicious attack. Tipically it involves
           compiling or simply checking source files for syntax errors.
        3) The actual runtime: run the code supplied by the user with several
           different examples and check the inputs and outputs in each case.
           This phase run the user supplied programs in a sandboxed
           environment by providing a very restricted user account.

    Notice that no code should depend on absolute paths, since they will run in
    some arbitrary working_dir in the filesystem.

    The approach took here sets the correct UID and GID and only works in
    POSIX systems.
    '''
    _vars = ['working_dir', 'is_prepared', 'timeout', 'username', 'password',
             'uid', 'gid', 'source_filename', 'build_command', 'run_command']

    def __init__(self, timeout=1.0):
        self.working_dir = TempFS()
        self.is_prepared = False
        self.timeout = timeout
        self.username = 'user_a'
        self.password = 'pipoca77'  # very bad?
        self._info = pwd.getpwnam(self.username)
        self.uid = self._info.pw_uid
        self.gid = self._info.pw_gid

    def vars(self):
        '''Return a dictionary of attributes that are used to compose values
        in user strings'''

        return {k: getattr(self, k, None) for k in self._vars}

    def syspath(self, path=''):
        '''Return the system working_dir for the temporary directory.

        This is useful for interacting with system functions. Creation and
        manipulation of files are better done through the TempFS object stored
        in the ``working_dir`` attribute.
        '''

        return self.working_dir.getsyspath(path)

    def prepare(self):
        '''Prepare all files for execution in an isolated environment.

        Return a Message object in case of failure or None in case of
        success.

        Subclasses must override the "_prepare" method that is called by this
        method.'''

        try:
            self._prepare()
        except Exception as ex:
            fmt = '%s(%s)' % (type(ex).__name__, ex)
            raise RuntimeError(
                ('Exception caught when preparing environment: %s\n'
                 'The _prepare() method must never raise exceptions.') % fmt)
        else:
            self._prepare_permissions()
            self.is_prepared = True

    def _prepare_permissions(self):
        '''Run chmod to change the ownership of all files in the prepared
        working directory'''

        os.chmod(self.syspath(), 0x755)

        return
        fs = self.working_dir
        paths = list(fs.walk())
        paths.reverse()

        for path, files in paths:
            for file in files:
                fpath = fs.getsyspath(file)
                os.chown(fpath, self.uid, self.gid)
            os.chown(path, self.uid, self.gid)

    def build(self):
        '''Build the executable (or simply check for syntax errors).

        Return a Message object in case of failure or None in case of
        success.

        Subclasses must override the "_build" method that is called by this
        method.'''

        with tempdir(self.working_dir.getsyspath('')):
            return self._build()

    def execute(self, inputs=()):
        '''Execute code passing the given sequence of input strings.

        Return a Message object that can represent a success of failure.

        Subclasses must override the "_execute" method that is called by this
        method.'''

        with tempdir(self.working_dir.getsyspath('')):
            return self._execute(inputs)

    _prepare = _build = lambda self: None
    _execute = lambda _self, inputs: None

    def _call_unprivileged(self, cmd, inputs, env={}, **kwds):
        '''Spawn a subprocess using the given command that runs in one of the
        unpriviledged "user_a", "user_b", etc accounts'''

        _env, env = env, dict(
            HOME=self.working_dir.getsyspath(''),
            LOGNAME=self.username,
            USER=self.username,
            PWD=self.working_dir.getsyspath(''),
        )
        env.update(_env)

        def preexec_fn():
            '''Configure process to run in the correct UID and GID'''

            info = pwd.getpwnam('nobody')
            os.setegid(info.pw_gid)
            os.seteuid(info.pw_uid)

        return subprocess.check_output(
            cmd,
            input=inputs,
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=self.timeout,
            # preexec_fn=preexec_fn,
            shell=True,
            env=env,
            **kwds)


class SourceSandbox(Sandbox):

    '''A sandboxed job based on the user sending a single file of source code
    for evaluation.

    Sub-classes must implement specific languages.
    '''

    source_filename = 'source.txt'
    build_command = None
    run_command = './{source_filename}'

    def __init__(self, source):
        self.source = source
        super().__init__()

    def _prepare(self):
        with self.working_dir.open(self.source_filename, 'w') as F:
            # F.write((
            #    'import os\n'
            #    'os.setuid(%s)\n'
            #    'os.setgid(%s)\n') % (self.uid, self.gid))
            F.write(self.source)
        #path = self.syspath(self.source_filename)

    def _build(self):
        os.system(self.build_command.format(**self.vars()))

    def _execute(self, inputs):
        cmd = self.run_command.format(**self.vars())
        inputs = self.password + '\n' + '\n'.join(inputs)
        try:
            output = self._call_unprivileged(cmd, inputs)
        except subprocess.CalledProcessError as ex:
            ex.output = ex.output[10:]
            return ErrorMessage(ex)
        else:
            return Message(output[10:], success=True)


class PyScriptSandbox(SourceSandbox):
    source_filename = 'source.py'
    build_command = None
    run_command = 'su {username} -c "python source.py"'

    def _build(self):
        try:
            compile(self.source, self.source_filename, 'exec')
        except SyntaxError as ex:
            return Message(ex)


class PytugaScriptSandbox(PyScriptSandbox):
    source_filename = 'source.pytg'
    build_command = None
    run_command = 'su {username} -c "pytuga source.pytg"'

    def _build(self):
        import pytuga
        src = pytuga.transpile(self.source)
        try:
            compile(src, self.source_filename, 'exec')
        except SyntaxError as ex:
            return Message(ex)


if __name__ == '__main__':
    src = "print('hello world')"
    #src = 'print("sum:", float(input("x: ")) + float(input("y: ")))'
    #src = 'x = 1\nwhile x:\n  x = input()\n  print(x)'
    #src = 'raise ValueError'
    job = PytugaScriptSandbox(src)
    job = PyScriptSandbox(src)
    job.prepare()
    job.build()
    print(job.execute(['1', '2']).render())
