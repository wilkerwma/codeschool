$(function() {
    // Make sortable-js understand the sync-api and sync-id attributes when
    // sorting
    $('sortable-js').on('update', function() {
        var state = this.sortable.toArray();
        var api_url = (this.attributes['sync-api'] || {}).nodeValue;
        var api_id = (this.attributes['sync-id'] || {}).nodeValue;

        if (api_url) {
            if (('' + this.__array_state) === ('' + state)) {
                return;
            }
            this.__array_state = state;
        }
        $.srvice(api_url, {owner_ref: api_id || null, order: state});
    });

    // Enable the remove button from sortable-remove classes
    $('sortable-js .sortable-remove')
        .fadeTo(1, 0.1)
        .hover(
            function() {$(this).fadeTo(0.1, 1)},
            function() {$(this).fadeTo(1, 0.1)}
        )
        .click(function () {
            var sortable = this.parentNode;
            var parent = this;
            while (sortable.nodeName !== 'SORTABLE-JS') {
                parent = sortable;
                sortable = sortable.parentNode;
            }
            parent.remove();
            sortable.fire('update');
        });

    // Multi-selectable paper menus
    document.createElement('paper-menu').constructor.prototype.selectedData = function() {
        return $.map(this.selectedItems, function(x) {
            return (x.attributes['data-id'] || {}).value;
        });
    }
});