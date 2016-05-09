/**
 * Define the encode(), decode(), dumps() and loads() functions
 */
var srvice$json = (function($) {
    /*
     * JSON conversions: traverse the object tree and encode or decode to a
     * JSON structure.
     */
    var json_converters = {
        // Javascript objects. You might need to encode if they have a "@type" key
        object: {
            constructor: Object,
            encode: function(x) {
                var out = {};

                for (key in x) {
                    out[key] = json_codec_worker(json[key], true);
                }

                return {'@': 'object', data: out};
            },
            decode: function(x) {
                return x.data || {};
            }
        },

        // Javascript dates
        date: {
            constructor: Date,
            encode: function(x) {
                return {
                    time: x.getTime(),
                    timezone: x.getTimezoneOffset()
                };
            },
            decode: function(x) {
                return new Date(x.time + x.timezone);
            }
        }
    };

    // Encode/decode JSON like structures. Do not follow inheritance since it tends
    // to be broken in js.
    function encode(x) {
        /**
         * Encode object into a JSON-compatible structure.
         */
        return json_codec_worker(x, true)
    }


    function decode(x) {
        /**
         * Return the Javascript object equivalent to the given JSON-compatible
         * structure.
         */
        return json_codec_worker(x, false)}


    function json_codec_worker(json, encode) {
        var decode = !encode;
        var out, key;

        // Don't like undefined values
        if (json === undefined) {
            throw "cannot " + (encode? "encode": "decode") + " undefined values";
        }

        // Return valid atomic types (but not subtypes)
        if (json === null) {
            return null;
        }

        if ([String, Number, Boolean].includes(json.constructor)) {
            return json;
        }

        // Convert arrays recursively
        if (json instanceof Array) {
            return $.map(json, function(x) {
                return [json_codec_worker(x, encode)];
            });
        }

        // Encode objects recursively
        if (json.constructor === Object && encode) {
            out = {};
            for (key in json) {
                out[key] = json_codec_worker(json[key], true);
            }
            if ('@' in json) {
                out = {'@': object, data: out};
            }
            return out;
        }

        // Decode objects
        if (json.constructor === Object && decode) {
            if ('@' in json) {
                var decoder = json['@'];
                delete json['@'];
                return  json_converters[decoder].decode(out);
            }

            out = {};
            for (key in json) {
                out[key] = json_codec_worker(json[key], false);
            }
            return out;
        }

        // Convert arbitrary JS types
        if (encode) {
            for (var name in  json_converters) {
                var conv =  json_converters[name];

                if (json.constructor === conv.constructor) {
                    var encoded = conv.encode(json);
                    encoded['@'] = name;
                    return encoded;
                }
            }
        }

        // Give up
        if (encode) {
            throw "cannot serialize to json: " + json;
        } else {
            throw "not a JSON element: " + json;
        }
    }


    function dumps(obj) {
        /**
         * Stringfy javascript object to a JSON stream.
         */

        var encoded = encode(obj);
        return JSON.stringify(encoded);
    }


    function loads(data) {
        /**
         * Load javascript object from a JSON encoded string.
         */

        var encoded = JSON.parse(data);
        return decode(encoded);
    }

    return {encode: encode, decode: decode, loads: loads, dumps: dumps}
}(jQuery));


/**
 * Utility functions
 */
srvice$util = (function($) {
    /**
     * Apply dialog-polyfill to dialog on unsupported browsers and display it
     * afterwards.
     *
     * @param dialog: <dialog> element
     */
    function dialogShowModal(dialog) {
        if (dialog.showModal === undefined) {
            dialogPolyfill.registerDialog(dialog);
        }
        dialog.showModal();
    }

    function byId(x) {
        return document.getElementById(x);
    }

    // Variadic function call. I am sure there is a better way to do this
    function varcall(func, args) {
        return func.apply(undefined, args); // does it work?

        //noinspection UnreachableCodeJS
        switch(args.length) {
            case undefined:
                throw "args must be an array";
            case 0:
                return func();
            case 1:
                return func(args[0]);
            case 2:
                return func(args[0], args[1]);
            case 3:
                return func(args[0], args[1], args[2]);
            case 4:
                return func(args[0], args[1], args[2], args[3]);
            case 5:
                return func(args[0], args[1], args[2], args[3], args[4]);
            case 6:
                return func(args[0], args[1], args[2], args[3], args[4], args[5]);
            case 7:
                return func(args[0], args[1], args[2], args[3], args[4], args[5], args[6]);
            case 8:
                return func(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7]);
            case 9:
                return func(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8]);
            case 10:
                return func(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], args[10]);
        }
        throw "not implemented: maximum of 10 variadic arguments";
    }

    function jsoncall(method, json) {
        // Execute with positional arguments
        if ('args' in json) {
            var args = json.args || [];
            delete json.args;

            if (!$.isEmptyObject(json)) {
                args[args.length] = json;
            }
            return varcall(method, args);
        }
        // Execute with a single object argument
        else {
            return method(json);
        }
    }

    return {byId: byId, varcall: varcall, jsoncall: jsoncall}
})(jQuery);


/**
 * Define srvice supported actions.
 */
var srvice$actions = (function($) {
    function statements(json) {
        for (var i = 0; i < json.data.length; i++) {
            srvice.exec(json.data[i]);
        }
    }

    function redirect(json) {
        if (json.as_link) {
            window.location.href = json.url;
        } else {
            window.location.replace(json.url);
        }
    }

    function dialog(json) {
        srvice.show_dialog(json.data, json);
    }

    function refresh() {
        window.location.replace('.');
    }

    function jquery(json) {
        var method;

        if (json.selector !== undefined) {
            method = $[json.action];
        } else {
            method = $(json.selector)[json.action];
            delete json.selector;
        }

        // Execute method
        if (method !== undefined) {
            throw 'invalid jQuery method: ' + json.action;
        }
        delete json.action;

        return jsoncall(method, json);
    }

    function jquery_chain(json){
        var action;
        var query = $(json.selector);
        for (var node in json.actions) {
            if (json.actions.hasOwnProperty(node)) {
                action = node.action;
                delete node.action;
                query = jsoncall(query[action], node);
            }
        }
        return query;
    }

    return {statements: statements, redirect: redirect, refresh: refresh,
            dialog:dialog, jquery_chain: jquery_chain };
})(jQuery);


var srvice = (function($) {
    var json = srvice$json;
    var actions = srvice$actions;
    var util = srvice$util;
    var byId = util.byId;

    // Remote call execution
    function srvice(api) {
        /**
         This function call some registered function in the server and return
         the result. Remember that all communication is done through JSON
         streams, hence all input arguments and the resulting value must be
         JSON-encodable.

         It can be called either with pure positional or pure named  arguments
         form.

         srvice('some-api-function*', {arg1: value1, arg2: value2, ...}):
            The most common form of remote call requires named arguments.

         srvice('some-api-function*', arg1, arg2, arg3, ...):
            This will call the remote api function with the given arguments and
            return the result. In order to use positional arguments, it is
            advisable to put an asterisk in the end of the api function name.
            The asterisk force the result to be interpreted as a positional
            call even if arg1 is a dictionary.

         This is the synchronous version. For an asynchronous version see
         :func:`srvice.async`.

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

         All exceptions raised in python-land are transmitted to javascript and
         are adapted and re-raised there.

        */
        var args = Array.prototype.slice.call(arguments, 1);

        // Temporary support to old-style calls
        // This will be dropped once all (or at least most) function calls
        // in codeschool are adapted.
        if (args.length === 2 &&
                args[0].constructor === Object &&
                args[1].constructor === Function &&
                api[api.length - 1] !== '*') {
            console.log('warning: deprecated call to srvice().');
            return srvice.__old_style(api, args[0], args[1]);
        }

        args = normalizeArgs(args, api);
        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: true,
            program: true
        });
    }

    srvice.value = function(api) {
        /**
         The asynchronous version of the srvice() function. This function
         returns a promise object and callback functions can be attached using
         the .then(), .done(), .fail(), etc methods::

             srvice.async('get-form', 'some-form-name'))
                .then(function(result) {
                    // do something with the result
                })
                .then(function(result) {
                    // do something else
                })
             ;
         */
        var args = Array.prototype.slice.call(arguments, 1);
        args = normalizeArgs(args, api);

        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: false,
            program: false,
            method: 'api'
        });
    };

    srvice.run = function(api) {
        /**
         The run() function calls a program marked with a ``srvice.program``
         decorator in Django. These "programs" encode a series of operations
         that should be carried out in the client.

         This call is asynchronous. For a synchronous version that blocks
         execution, please see srvice.runSync().

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

         The default behavior is to execute asynchronously, unless the second
         async parameter is true.
         */
        if (async === undefined) {
            async = true;
        }

        return srvice.rpc({
            api: api,
            args: args[0],
            kwargs: args[1],
            async: async,
            program: true,
            result: null,
            method: 'js'
        });
    };


    srvice.html = function(api) {
        /**
         Retrieve HTML data from a registered srvice template by passing the
         given arguments.

         Returns:
            A promise object.
         */
    };


    srvice.htmlTo = function(api, selector) {

    };


    srvice.rpc = function(args) {
        /**
         The workhorse behind srvice(), srvice.async(), srvice.run(), and
         srvice.runSync() functions. It receives a single dictionary argument
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
            Can be any of 'api', 'program', or 'js'.
         program:
            If true (default), execute any received programatic instructions.
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
            server: srvice.serverUri,
            async: true,
            program: true,
            errors: true,
            timeout: 1
        }, args);

        // Check consistency
        if (args.api === undefined) {
            throw TypeError('must define an api function');
        }

        // Create the payload
        var payload = {args: args.args, kwargs: args.kwargs};
        console.log(payload);
        payload = json.dumps(payload);
        console.log(payload);

        // Function to process resulting payload
        function processResult(received) {
            received = json.decode(received);
            var error = received.error;
            var data = received.data;
            var program = received.program;
            var context = {};

            if (program !== undefined) {
                //noinspection JSUnusedAssignment
                context = processProgram(program);
            }
            if (args.errors && error) {
                throw processError(error);
            }
            return data;
        }

        processResult(payload);

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

    /**
     * Make calls to a JSON rpc
     */
    srvice.__old_style = function(api, data, callback) {
        var result = [null];
        var async;

        if (callback === true) {
            async = false;
            callback = function(x) {result[0] = x};
        } else {
            async = true;
        }

        $.ajax({
            url: conf.url + api,
            type: "POST",
            async: async,
            contentType: "application/json",
            dataType: "application/json",
            data: JSON.stringify(json.encode(data)),
            complete: function (data) {
                if (data.status !== 200) {
                    throw data.responseText;
                }
                data = JSON.parse(data.responseText);

                if (data["exec"] !== undefined) {
                    exec_action(json["exec"]);
                }

                if (data["result"] !== undefined) {
                    if (callback !== undefined) {
                        callback(json.decode(data["result"]));
                    }
                }
                else if (data["error"] !== undefined) {
                    throw data["error"] + ": " + data["error-message"]
                }
            }
        });

        return result[0];
    };


    ////////////////////////////////////////////////////////////////////////////
    //                              DIALOGS                                   //
    ////////////////////////////////////////////////////////////////////////////
    function _asDialog(elem) {
        if (elem.showModal === undefined) {
            dialogPolyfill.registerDialog(elem);
        }
        return elem;
    }

    function _getDialog(opt, action) {
        var opt = opt || {};
        var dialog = opt.dialog || byId(opt.dialogId || 'dialog');
        var content = opt.dialogContent || byId(opt.dialogContentId || 'dialog-content');

        if (dialog === undefined) {
            dialog = document.createElement('DIALOG');
            dialog.id = 'dialog';
            document.body.appendChild(dialog);
        }
        if (content === undefined) {
            content = document.createElement('DIV');
            content.id = 'dialog-content';
            dialog.appendChild(content);
        }

        // Add content from html element, if given
        var html = opt.html;
        if (opt.sourceId) {
            html = (html || '') + byId(opt.sourceId).innerHTML;
        }

        if (opt.url) {
            // Append html in url
            $.ajax(options.url, {
                method: 'GET',
                dataType: 'text',
                complete: function(data) {
                    $(content).html((html || '') + data.responseText);
                    action(dialog);
                }
            });
        }
        else {
            if (html !== undefined) {
                $(content).html(html);
            }
            action(dialog);
        }
    }

    /**
     Show dialog with some content.

     It accept the following named arguments.

     Keyword Args:
        dialog:
            The dialog element.
        dialogId:
            The id for the dialog element. The default is 'dialog'. It creates
            a new dialog and appends to body if no dialog is set.
        dialogContent:
            A child element of dialog that should hold the html content.
        dialogContentId:
            The id for dialogContent. The default is 'dialog-content'. If no
            dialog content is specified, it creates a <div id="dialog-content">
            and append to the dialog.
        html:
            The inner HTML text for the dialog-content.
        sourceId:
            If given, represents the id from an html element whose innerHTML
            should be copied to dialogContent element.
        url:
            If given, represents the url that will be used to fetch html data
            and inssert in the dialogContent innerHTML.

     Return:
        This function is executed async and does not return anything.

     */
    srvice.openDialog = function(options) {
        _getDialog(options, function(dialog) {
            _asDialog(dialog).showModal();
        });
    };

    /**
     * Hide dialog.
     *
     * Accept the same arguments as the openDialog() function.
     */
    srvice.closeDialog = function(options) {
        _getDialog(options, function(dialog) {
            _asDialog(dialog).close();
        });
    };

    /**
     * Toggle dialog visibility.
     *
     * Accept the same arguments as the openDialog() function.
     */
    srvice.toggleDialog = function(options) {
        _getDialog(options, function(dialog) {
            dialog = _asDialog(dialog);
            if (dialog.open) {
                dialog.close()
            }
            else {
                dialog.showModal();
            }
        });
    };

    /**
     Modify dialog.

     Has two signatures:

     srvice.dialog(action, html, options):
        Perform one of 'open', 'close', 'toggle' actions on the dialog.
        The user can pass an additional html data and a dictionary of named
        arguments with the same meaning as in :func:`srvice.openDialog()`.
     srvice.dialog(options):
        ``options`` is a dictionary of named  arguments with the same meaning
        as in :func:`srvice.openDialog()`.

     */
    srvice.dialog = function(action, text, options) {
        if (action instanceof Object) {
            options = action || {};
            action = options.action || 'toggle';
        } else {
            options = options || {};
            options.text = text;
        }

        if (action == 'open') {
            return srvice.openDialog(options);
        }
        else if (action == 'close') {
            return srvice.closeDialog(options);
        }
        else if (action == 'toggle') {
            return srvice.toggleDialog(options);
        }
        else {
            throw Error('invalid dialog action: ' + action);
        }
    };


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
    function normalizeArgs(args, api) {
        if (api[api.length - 1] === '*') {
            return [args, {}];
        } else if (args.length == 0) {
            return [[], {}];
        } else if (args.length == 1 && args[0] instanceof Object) {
            return [[], args[0]];
        } else {
            return [args, {}];
        }
    }

    $.srvice = srvice;
    srvice.serverUri = '/srvice';
    srvice.do = srvice$actions;
    return srvice;
})(jQuery);

