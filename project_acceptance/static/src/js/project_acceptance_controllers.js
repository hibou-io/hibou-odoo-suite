odoo.define('project_acceptance.AcceptanceFormController', function (required) {
    "use stric";
    var FormController = require('web.FormController');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var AcceptanceFormController = FormController.extend({
        events: _.extend({}, FormController.prototype.events, {
            'click .o_account_followup_manual_action_button': '_onManualAction',
        }),
        _onManualAction: function (){

        },
    })
   
})

// odoo.define('project_acceptance.ProjectAcceptanceButton', function(require) {
//     'use strict';

//     const ProjectAcceptanceButton = require('point_of_sale.ProjectAcceptanceButton');
//     const Registries = require('point_of_sale.Registries');

//     const FormProjectAcceptanceButton = ProjectAcceptanceButton =>
//         class extends ProjectAcceptanceButton {

//         };

//     Registries.Component.extend(ProjectAcceptanceButton, FormProjectAcceptanceButton);

//     return ProjectAcceptanceButton;
// });
