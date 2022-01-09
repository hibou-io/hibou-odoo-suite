odoo.define('timesheet_grid_work_entry.TimerHeaderM2O', function (require) {
"use strict";

console.log('timesheet_grid_work_entry.TimerHeaderM2OWorkEntry v1');

const config = require('web.config');
const core = require('web.core');
const relational_fields = require('web.relational_fields');
const Widget = require('web.Widget');

const Many2One = relational_fields.FieldMany2One;
const _t = core._t;
const TimerHeaderM2O = require('timesheet_grid.TimerHeaderM2O');

const TimerHeaderM2OWorkEntry = Widget.include(TimerHeaderM2O, {

    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} params
     */
    init: function (parent, params) {
        console.log('TimerHeaderM2OWorkEntry.init v1');
        this._super(...arguments);
        // StandaloneFieldManagerMixin.init.call(this);
        // this.projectId = arguments[1];
        // this.taskId = arguments[2];
        this.workTypeId = arguments[3];
    },

    /**
     * @override
     */
    willStart: async function () {
        await this._super(...arguments);

        const workTypeDomain = [['allow_timesheet', '=', true]];
        this.workType = await this.model.makeRecord('account.analytic.line', [{
            name: 'work_type_id',
            relation: 'hr.work.entry.type',
            type: 'many2one',
            value: this.projectTypeId,
            domain: workTypeDomain,
        }]);

    },
    /**
     * @override
     */
    start: async function () {
        const _super = this._super.bind(this);
        let placeholderWorkType;

        if (config.device.isMobile) {
            placeholderWorkType = _t('Work Type');
        } else {
            placeholderWorkType = _t('Select a Work Type');
        }
        const workTypeRecord = this.model.get(this.workType);
        const workTypeMany2one = new Many2One(this, 'work_type_id', workTypeRecord, {
            attrs: {
                placeholder: placeholderWorkType,
            },
            noOpen: true,
            noCreate: true,
            mode: 'edit',
            required: true,
        });
        workTypeMany2one.field['required'] = true;
        this._registerWidget(this.workType, 'work_type_id', workTypeMany2one);
        await workTypeMany2one.appendTo(this.$('.timer_work_type_id'));
        this.workTypeMany2one = workTypeMany2one;

        _super.apply(...arguments);
    },
    /**
     * @private
     * @override
     * @param {OdooEvent} ev
     */
    _onFieldChanged: async function (ev) {
        await this._super(...arguments);

        const workType = this.workTypeId;
        const fieldName = ev.target.name;

        if (fieldName === 'work_type_id') {
            record = this.model.get(this.workType);
            var newId = record.data.work_type_id.res_id;
            if (workType !== newId) {
                this.workTypeId = newId;
            }
        }

        // } else if (fieldName === 'task_id') {
        //     record = this.model.get(this.task);
        //     const newId = record.data.task_id && record.data.task_id.res_id;
        //     if (task !== newId) {
        //         let project_id = this.projectId;
        //         if (!project_id) {
        //             const task_data = await this._rpc({
        //                 model: 'project.task',
        //                 method: 'search_read',
        //                 args: [[['id', '=', newId]], ['project_id']],
        //             });
        //             project_id = task_data[0].project_id[0];
        //         }

        //         this.taskId = false;
        //         this.trigger_up('timer-edit-task', {'taskId': newId, 'projectId': project_id});
        //     }
        // }
    },
});

return TimerHeaderM2OWorkEntry

});
