odoo.define('web_auto_paginate.action_manager', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');

    ActionManager.include({
        _executeCloseAction: function (action, options) {
            if (action.auto_paginate) {
                var $_o_pager_next = $('button.o_pager_next');
                if ($_o_pager_next.length >= 1) {
                    setTimeout(function(){$_o_pager_next[0].click()}, 500)
                }
            }
            return this._super(action, options);
        }
    });

    return ActionManager;
});
