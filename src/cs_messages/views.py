from django.shortcuts import render
import srvice


@srvice.program
def message_manager(client, pk, action='get'):
    """
    Manage messages using AJAX.

    The 'action' attribute can assume the following values:

        get:
            Fetch a list of messages from the server.
        clear:
            Mark all messages as inactive.
    """

    if action == 'error':
        user = user.