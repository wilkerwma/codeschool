// Bind to jQuery
var srvice = (function($) {
    /**
     * Utility functions
     */
    function byId(x) {return document.getElementById(x)}


    // Variadic function call. I am sure there is a better way to do this
    function varcall(func, args) {
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

    /*
     * JSON conversions: traverse the object tree and encode or decode to a
     * JSON structure.
     */
    var json_converters = {
        // Javascript objects. You might need to encode if they have a "@type" key
        object: {
            constructor: Object,
            encode: function(x) {
                return {'@type': 'object', data: object};
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
                    offset: x.getTimezoneOffset()
                };
            },
            decode: function(x) {
                return new Date(x.time + x.offset);
            }
        }
    };

    // Encode/decode JSON like structures. Do not follow inheritance since it tends
    // to be broken in js.
    function encode(x) {return json_codec_worker(x, true)}
    function decode(x) {return json_codec_worker(x, false)}
    function json_codec_worker(json, encode) {
        // Don't like undefined values
        if (json === undefined) {
            throw "cannot " + (encode? "encode": "decode") + " undefined values";
        }

        // Return valid atomic types (but not subtypes)
        if (json === null) {
            return null;
        }
        else if ([String, Number, Boolean].includes(json.constructor)) {
            return json;
        }

        // Convert arrays recursively
        else if (json instanceof Array) {
            return $.map(json, function(x) {
                return [json_codec_worker(x, encode)];
            });
        }

        // Encode/decode objects recursively
        else if (json.constructor === Object) {
            var out = {};
            for (var key in json) {
                if (json.hasOwnProperty(key)) {
                    out[key] = json_codec_worker(json[key], encode);
                }
            }

            if (encode) {
                return ('@type' in json) ? {'@type': 'object', data: out} : out;
            }
            else if ('@type' in json) {
                return  json_converters[json['@type']].decode(out);
            } else {
                return out;
            }
        }

        // Convert arbitrary JS types
        else if (encode) {
            for (var name in  json_converters) {
                if ( json_converters.hasOwnProperty(name)) {
                    var conv =  json_converters[name];

                    if (json.constructor === conv.constructor) {
                        var encoded = conv.encode(json);
                        encoded['@type'] = name;
                        return encoded;
                    }
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
            result = simple(decode(json.data));
        }
        // Try actions dispatch or jquery dispatch if method isn't found
        else {
            var method = actions[action.replace("-", "_")];
            json = decode(json);

            if (method !== undefined) {
                return method(json)
            } else {
                return actions.jquery(json);
            }
        }

        // Process result
        return (result !== undefined)? encode(result): null;
    }

    var actions = {
        statements: function (json) {
            for (var i = 0; i < json.data.length; i++) {
                srvice.exec(json.data[i]);
            }
        },

        redirect: function (json) {
            if (json.as_link) {
                window.location.href = json.url;
            } else {
                window.location.replace(json.url);
            }
        },

        dialog: function (json) {
            srvice.show_dialog(json.data, json);
        },

        refresh: function (json) {
            window.location.replace('.');
        },

        jquery: function(json) {
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
        },

        jquery_chain: function(json){
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
    };

    /**
     * Make calls to a JSON rpc
     */
    function srvice(api, data, callback) {
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
            data: JSON.stringify(encode(data)),
            complete: function (data) {
                if (data.status !== 200) {
                    throw data.responseText;
                }
                var json = JSON.parse(data.responseText);

                if (json["exec"] !== undefined) {
                    exec_action(json["exec"]);
                }

                if (json["result"] !== undefined) {
                    if (callback !== undefined) {
                        callback(decode(json["result"]));
                    }
                }
                else if (json["error"] !== undefined) {
                    throw json["error"] + ": " + json["error-message"]
                }
            }
        });

        return result[0];
    }
    srvice.call = srvice;
    $.srvice = srvice;

    /**
     * Configuration
     */
    var conf = {
        url: '/srvice/'
    };

    srvice.setConf = function(key, value) {
        conf[key] = value;
    };

    /**
     * $srvice namespace
     */
    srvice.callExternal = function(url, api, data, callback) {
        var sysurl = conf.url;
        var result;

        try {
            conf.url = url;
            result = srvice(api, data, callback);
        }
        finally {
            conf.url = sysurl;
        }
        return result;
    };

    srvice.dialog = function(action, text, options) {
        // Process options
        if (action instanceof Object) {
            options = action || {};
        } else {
            options = options || {};
            options.action = action;
            options.text = text;
        }

        // Update default options
        var conf = $.extend({
            action: 'toggle',
            text: '',
            dialogId: 'dialog',
            dialogContentId: 'dialog-content',
            url: null
        }, options);

        // Fetch elements
        var dialog = document.getElementById(conf.dialogId);
        var content = document.getElementById(conf.dialogContentId);

        // Select action
        if (conf.action === 'toggle') {
            if (dialog === undefined) {
                conf.action = 'open';
            } else {
                var opened = (dialog.opened === undefined)? !dialog.hidden: dialog.opened;
                conf.action = opened? 'close': 'open';
            }
        }

        // Close dialog
        if (conf.action === 'close') {
            if (dialog.close) {
                dialog.close()
            } else {
                dialog.hidden = true;
            }
            return;
        }

        // Create dialog if it does not exist
        if (!dialog || !content) {
            alert('not implemented: cannot create main dialog from scratch');
            throw 'not implemented';
        }

        // Normalize dialog opening
        function open_dialog() {
            if (dialog.open) {
                dialog.open();
            } else {
                dialog.hidden = false;
            }
        }

        // Add content from url, if given
        if (options.url) {
            $.ajax(options.url, {
                method: 'GET',
                dataType: 'text',
                complete: function(data) {
                    $(content).html(conf.text + data.responseText);
                    open_dialog();
                }
            });
        } else {
            $(content).html(conf.text);
            open_dialog();
        }
    };

    return srvice;
})(jQuery);

