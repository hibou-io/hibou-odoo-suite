odoo.define('timesheet_grid_work_entry.TimerGridView', function (require) {
    "use strict";

    console.log('timesheet_grid_work_entry.TimerGridView v1');

    const viewRegistry = require('web.view_registry');
    const WebGridView = require('web_grid.GridView');
    const TimerGridController = require('timesheet_grid.TimerGridController');
    const TimerGridModel = require('timesheet_grid.TimerGridModel');
    const GridRenderer = require('timesheet_grid_work_entry.TimerGridRenderer');
    const TimesheetConfigQRCodeMixin = require('timesheet_grid.TimesheetConfigQRCodeMixin');
    const { onMounted, onPatched } = owl.hooks;

    class TimerGridRenderer extends GridRenderer {
        constructor() {
            console.log('TimerGridRenderer constructor called');
            super(...arguments);
            onMounted(() => this._bindPlayStoreIcon());
            onPatched(() => this._bindPlayStoreIcon());
        }
    }

    // QRCode mixin to bind event on play store icon
    Object.assign(TimerGridRenderer.prototype, TimesheetConfigQRCodeMixin);

    const TimerGridView = WebGridView.extend({
        config: Object.assign({}, WebGridView.prototype.config, {
            Model: TimerGridModel,
            Controller: TimerGridController,
            Renderer: TimerGridRenderer
        })
    });

    viewRegistry.add('timesheet_timer_grid', TimerGridView);

    return TimerGridView;
});
