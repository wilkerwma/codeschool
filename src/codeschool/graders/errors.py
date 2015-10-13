class GradingError(Exception):

    '''Base class for all errors that may occur during grading.'''


class BadSyntaxError(GradingError):

    '''Flags a syntax error in the input code.'''


class BadValueError(GradingError):

    '''Code runs correctly, but computes wrong output values.'''


class UnexpectedError(GradingError):

    '''Code terminates with a segfault, uncaught exception, or any other
    non-zero exit code.'''


class PresentationError(GradingError):

    '''Flags code that runs without errors and has the correct input/output
    sequence, but values are presented incorrectly.'''


class TimeExceededError(GradingError):

    '''Flags code that do not terminate until the maximum estipulated
    runtime.'''


class DidNotTerminateError(GradingError):

    '''Flags code that do not terminate when expected.'''


class EarlyTerminationError(GradingError):

    '''Flags code that terminate earlier than expected.'''
