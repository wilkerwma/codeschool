// Utility functions
srvice$util = (function($) {
    /**
     * Apply dialog polyfill to dialog on unsupported browsers and display it
     * afterwards.
     *
     * @param dialog - <dialog> element.
     */
    function dialogShowModal(dialog) {
        if (dialog.showModal === undefined) {
            dialogPolyfill.registerDialog(dialog);
        }
        dialog.showModal();
    }

    /**
     * Shortcut to document.getElementById()
     */
    function byId(x) {
        return document.getElementById(x);
    }

    /**
     * Variadic function call.
     */
    function varcall(func, args) {
        // I am sure there is a better way to do this
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