Srvice is a Python/Javascript library that aims be a bridge between the client
running javascript and the server running Django. It defines a RPC interface in
which the client can make calls to a Django server in a very transparent way.
The server may also send instructions to execute arbitrary actions in the
client.

Example
=======

Consider the HTML bellow that shows a list of users::

    <ul class="friends">
        <li id="friend-johnwl">John [<button onclick="unfriend('johnwl')">unfriend</button>]</li>
        <li id="friend-paulmc">Paul [<button onclick="unfriend('paulmc')">unfriend</button>]</li>
        ...
    </ul>

The "unfriend" button should remove the chosen friend from the list and tell the
server to update the database. Using srvice we can implement the javascript
``unfriend`` function simply as:

.. code:: javascript

    function unfriend(username) {
        srvice('unfriend', username);
    }

The logic runs in the server::

    import ...

    @srvice.program
    def unfriend(client, username):
        friend = Users.objects.get(username=username)
        client.user.unfriend(friend)
        del client['#friend-%s' % username]
        client.dialog('friend removed!')

All operations in the ``client`` object are registered and compiled to
javascript to be executed in the client. In this case, it generates a file
similar to this one::

.. code:: javascript

    var __v1 = jQuery('#friend-johnwl').delete();
    dialog('friend removed');


