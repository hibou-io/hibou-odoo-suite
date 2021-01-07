odoo.define('web_auto_paginate.action_manager', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');

    ActionManager.include({
        _executeCloseAction: function (action, options) {
            var res = this._super(action, options);
            if (action.auto_paginate) {
                res.then(auto_next_record);
            }
            return res;
        }
    });

    function auto_next_record() {
        var $_o_pager_next = $('button.o_pager_next');
        if ($_o_pager_next.length >= 1) {
            $_o_pager_next = $_o_pager_next[0];
            $_o_pager_next.click();
        }
    }

    return ActionManager;
});
