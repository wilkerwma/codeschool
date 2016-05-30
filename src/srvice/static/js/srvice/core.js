var srvice = (function($) {
    var json = srvice$json;
    var actions = srvice$actions;
    var util = srvice$util;
    var byId = util.byId;

    // Remote call execution
    function srvice() {
        /**
         This function call some registered function in the server and return
         the result. Remember that all communication is done through JSON
         streams, hence all input arguments and the resulting value must be
         JSON-encodable.

         It can be called either with a pure positional or pure named arguments
         form.

         srvice('some-remote-api', {arg1: value1, arg2: value2, ...}):
            The most common form of remote call requires named arguments.

         srvice('some-remote-api*', arg1, arg2, arg3, ...):
            This will call the remote api function with the given arguments and
            return the result. In order to use positional arguments, it is
            advisable to put an asterisk in the end of the api function name.
            The asterisk forces the result to be interpreted as a positional
            call even if arg1 is a dictionary.

         This function returns a promise object and callback functions can be
         attached to it using the .then(), .done(), .fail(), etc methods::

             srvice('get-user-data', 'foobar123'))
                .then(function(result) {
                        // do something with the result
                    })
                .then(function(result) {
                        // do something else
                    });

         srvice also defines an additional method .value() that can be called to
         return the value of the computation in a synchronous fashion. This kind
         of code should be avoided, but it is nevertheless available in case it
         is necessary.

         In Django, api functions are registered using the @srvice.api
         decorator to a function. These functions always receive a request as
         the first argument, followed by the arguments passed from javascript.
         The return value is transmitted back to the client and returned to the
         caller.

         .. code:: python
            import srvice

            @srvice.api
            def function(request, arg1, arg2, arg3, ...):
                ...
                return value

         All exceptions raised in python-land are transmitted to javascript,
         adapted, and re-raised there.

        */
        return srvice_call(arguments, {});
    }

    srvice.run = function(api) {
        /**
         The run() function calls a remote function marked with a
         ``@srvice.program`` decorator in Django. These "programs" encode a
         series of operations that should be carried out in the client.

         A program is defined in Django using the decorator:

         .. code:: python
             import srvice

             @srvice.program
             def program(client, arg1, arg2, ...):
                 if client.request.user is None:
                     raise PermissionError

                 client.alert("this will trigger a js alert in the client!")
                 client.jquery('div').hide()
                 client.js('console.log("foo bar")')
                 return None

         The client in python object exposes all functions that exist in the
         srvice object in javascript.
         */

        var args = Array.prototype.slice.call(arguments, 1);
        args = normalizeArgs(args, api);

        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: true,
            program: true,
            method: 'program'
        });
    };

    srvice.js = function(api) {
        /**
         Execute the javascript source code in the given API point in an
         isolated namespace.

         In Django, functions are registered using the @srvice.js decorator::

         .. code:: python
            import srvice

            @srvice.js
            def js_maker(request, arg1, arg2, arg3, ...):
                return string_of_javascript_code()

         */
        var args = Array.prototype.slice.call(arguments, 1);
        args = normalizeArgs(args, api);

        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: true,
            program: false,
            method: 'js'
        });
    };


    srvice.html = function(api) {
        /**
         Retrieve HTML data from a registered srvice template by passing the
         given arguments.

         In Django, functions are registered using the @srvice.html decorator::

         .. code:: python
            import srvice

            @srvice.html
            def js_maker(request, arg1, arg2, arg3, ...):
                return string_of_html_source()

         */

        var args = Array.prototype.slice.call(arguments, 1);
        args = normalizeArgs(args, api);

        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: true,
            program: false,
            method: 'html'
        });
    };


    srvice.htmlTo = function(api, selector) {
        /**
         Similar to srvice.html. However, the second argument is a CSS selector
         for the elements that will receive the resulting html code.
         */
        var args = Array.prototype.slice.call(arguments, 2);
        args = normalizeArgs(args, api);

        value = srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: true,
            program: false,
            method: 'html'
        });

        value.success(function(html) {
            $(selector).html(html);
        })
        return value;
    };


    srvice.rpc = function(args) {
        /**
         The workhorse behind srvice(), srvice.run(), srvice.js() and
         srvice.html() functions. It receives a single dictionary argument
         that understands the following parameters:

         api:
            Api name of the called function/program
         args:
            List of positional arguments to be passed to the calling function.
         kwargs:
            An object with all the named arguments.
         server:
            Override the default server root. Usually srvice will open the URL
            at http://<localdomain>/srvice/api-function-name.
         async:
            If true, returns a promise. Otherwise, it blocks execution and
            returns the result of the function call.
         method:
            Can be any of 'api', 'program', 'js', or 'html'.
         program:
            If true (default), execute any received programmatic instructions.
         error:
            If true (default), it will raise any exceptions raised by the remote
            call.
         result:
            If given, will determine the result value of the function call.
         timeout:
            Maximum amount of time (in seconds) to wait for a server response.
            Default to 30.0.
         */

        // Initialize parameters
        args = $.extend({
            api: undefined,
            args: [],
            kwargs: {},
            async: true,
            program: true,
            errors: true,
            timeout: 5,
            method: 'POST'
        }, args);

        // Check consistency
        if (args.api === undefined) {
            throw TypeError('must define an api function');
        }

        // Create the payload
        var payload = {api: args.api, args: args.args, kwargs: args.kwargs};
        payload = json.dumps(payload);

        // Create ajax promise object
        var promise = $.ajax({
            url: args.api,
            data: payload,
            type: args.method,
            dataType: 'json'
        });

        // Register program processor
        if (args.program) {
            promise.done(function(result) {
                if (result.program) {
                    processProgram(result.program);
                }
            });
        }

        // Register error processor
        if (args.errors) {
            promise.done(function(result) {
                if (result.errors) {
                    processErrors(result.errors);
                }
            });
        }

        return promise;
    };


    /**
     * Execution of JSON encoded actions.
     */
    var exec_simple_raw = {eval: eval};
    var exec_simple = {alert: alert};

    // Main entry point for execution/processing of JSON data
    function exec_action(json) {
        var result;
        var action = json.action;

        // Dispatch method call
        var raw = exec_simple_raw[action];
        var simple = exec_simple[action];

        if (raw !== undefined) {
            result = raw(json.data);
        }
        else if (simple !== undefined) {
            result = simple(json.decode(json.data));
        }
        // Try actions dispatch or jquery dispatch if method isn't found
        else {
            var method = actions[action.replace("-", "_")];
            json = json.decode(json);

            if (method !== undefined) {
                return method(json)
            } else {
                return actions.jquery(json);
            }
        }

        // Process result
        return (result !== undefined)? encode(result): null;
    }


    ////////////////////////////////////////////////////////////////////////////
    //                              ???????                                   //
    ////////////////////////////////////////////////////////////////////////////
    srvice.go = function(url, replace) {
        if (replace) {
            window.location.replace(url);
        } else {
            window.location.href = url;
        }
    };

    // Auxiliary function used to normalize input arguments to many srvice
    // methods.
    function srvice_call(args, options) {
        var api = args[0];
        args = Array.prototype.slice.call(args, 1);

        if (api[api.length - 1] === '*') {
            kwargs = {}
        } else if (args.length == 0) {
            args = [];
            kwargs = {};
        } else if (args.length == 1 && args[0] instanceof Object) {
            kwargs = args[0];
            args = [];
        } else {
            kwargs = {};
        }

        // Normalize api name
        if (api[api.length -1] !== '/') {
            api = api + '/';
        }

        // Create promise and attach value() method
        var promise = srvice.rpc($.extend({
            api: api,
            args: args,
            kwargs: kwargs
        }, options));

        promise.value = function() {

        };
        return promise;
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });


    $.srvice = srvice;
    srvice.serverUri = '/srvice';
    srvice.do = srvice$actions;
    return srvice;
})(jQuery);

