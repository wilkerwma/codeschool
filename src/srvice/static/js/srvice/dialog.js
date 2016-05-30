srvice$dialog = (function($) {
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
                complete: function (data) {
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
         and insert in the dialogContent innerHTML.

     Return:
        This function is executed async and does not return anything.

     */
    srvice.openDialog = function (options) {
        _getDialog(options, function (dialog) {
            _asDialog(dialog).showModal();
        });
    };

    /**
     * Hide dialog.
     *
     * Accept the same arguments as the openDialog() function.
     */
    srvice.closeDialog = function (options) {
        _getDialog(options, function (dialog) {
            _asDialog(dialog).close();
        });
    };

    /**
     * Toggle dialog visibility.
     *
     * Accept the same arguments as the openDialog() function.
     */
    srvice.toggleDialog = function (options) {
        _getDialog(options, function (dialog) {
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
    srvice.dialog = function (action, text, options) {
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
}(jQuery));