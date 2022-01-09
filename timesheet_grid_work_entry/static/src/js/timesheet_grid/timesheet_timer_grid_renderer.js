odoo.define('timesheet_grid_work_entry.TimerGridRenderer', function (require) {
    "use strict";

    console.log('timesheet_grid_work_entry.TimerGridRenderer v1');

    const utils = require('web.utils');
    const GridRenderer = require('web_grid.GridRenderer');
    const TimerHeaderComponent = require('timesheet_grid_work_entry.TimerHeaderComponent');
    const TimerStartComponent = require('timesheet_grid.TimerStartComponent');
    const { useState, useExternalListener, useRef } = owl.hooks;

    class TimerGridRenderer extends GridRenderer {
        constructor(parent, props) {
            super(...arguments);
            useExternalListener(window, 'keydown', this._onKeydown);
            useExternalListener(window, 'keyup', this._onKeyup);

            this.initialGridAnchor = props.context.grid_anchor;
            this.initialGroupBy = props.groupBy;

            this.stateTimer = useState({
                taskId: undefined,
                taskName: '',
                projectId: undefined,
                projectName: '',
                workTypeId: undefined,
                workTypeName: '',
                addTimeMode: false,
                description: '',
                startSeconds: 0,
                timerRunning: false,
                indexRunning: -1,
                readOnly: false,
                projectWarning: false,
            });
            this.timerHeader = useRef('timerHeader');
            this.timesheetId = false;
            this._onChangeProjectTaskDebounce = _.debounce(this._setProjectTask.bind(this), 500);
        }
        mounted() {
            super.mounted(...arguments);
            if (this.formatType === 'float_time') {
                this._get_running_timer();
            }
        }
        async willUpdateProps(nextProps) {
            if (nextProps.data !== this.props.data) {
                this._match_line(nextProps.data);
            }
            return super.willUpdateProps(...arguments);
        }

        //----------------------------------------------------------------------
        // Getters
        //----------------------------------------------------------------------

        /**
         * @returns {boolean} returns true if when we need to display the timer button
         *
         */
        get showTimerButton() {
            return ((this.formatType === 'float_time') && (
                this.props.groupBy.includes('project_id')
            ));
        }
        /**
         * @returns {boolean} returns always true if timesheet in hours, that way we know we're on a timesheet grid and
         * we can show the timer header.
         *
         */
        get showTimer() {
            return this.formatType === 'float_time';
        }

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        _match_line(new_grid) {
            const grid = (new_grid) ? new_grid[0].rows : this.props.data[0].rows;
            let current_value;
            for (let i = 0; i < grid.length; i++) {
                current_value = grid[i].values;
                if (current_value.project_id && current_value.project_id[0] === this.stateTimer.projectId
                    && ((!current_value.task_id && !this.stateTimer.taskId) ||
                    (current_value.task_id && current_value.task_id[0] === this.stateTimer.taskId))) {
                    this.stateTimer.indexRunning = i;
                    return;
                }
            }
            this.stateTimer.indexRunning = -1;
        }
        async _get_running_timer() {
            const result = await this.rpc({
                model: 'account.analytic.line',
                method: 'get_running_timer',
                args: []
            });
            if (result.id !== undefined) {
                this.stateTimer.timerRunning = true;
                this.timesheetId = result.id;
                this.stateTimer.readOnly = result.readonly;
                this.stateTimer.projectId = result.project_id;
                this.stateTimer.taskId = result.task_id || undefined;

                // In case of read-only timer
                this.stateTimer.projectName = (result.project_name) ? result.project_name : '';
                this.stateTimer.taskName = (result.task_name) ? result.task_name : '';

                this.stateTimer.timerRunning = true;
                this.stateTimer.description = (result.description === '/') ? '' : result.description;
                this.stateTimer.startSeconds = Math.floor(Date.now() / 1000) - result.start;
            } else if (this.stateTimer.timerRunning && this.stateTimer.projectId) {
                this.timesheetId = false;
                this.stateTimer.readOnly = false;
                this.stateTimer.projectId = false;
                this.stateTimer.taskId = undefined;

                this.stateTimer.timerRunning = false;
                this.stateTimer.description = '';
            }
            if (this.timerHeader.comp.startButton.el) {
                this.timerHeader.comp.startButton.el.focus();
            }
            this._match_line();
        }
        async _onSetProject(data) {
            this.stateTimer.projectId = data.detail.projectId;
            this.stateTimer.taskId = undefined;
            this._onChangeProjectTaskDebounce(data.detail.projectId, undefined);
        }
        async _onSetWorkType(data) {
            this.stateTimer.workTypeId = data.detail.workTypeId;
        }
        async _onSetTask(data) {
            this.stateTimer.projectId = data.detail.projectId;
            this.stateTimer.taskId = data.detail.taskId || undefined;
            this._onChangeProjectTaskDebounce(this.stateTimer.projectId, data.detail.taskId);
        }
        async _setProjectTask(projectId, taskId) {
            if (!this.stateTimer.projectId) {
                return;
            }
            if (this.timesheetId) {
                const timesheetId = await this.rpc({
                    model: 'account.analytic.line',
                    method: 'action_change_project_task',
                    args: [[this.timesheetId], this.stateTimer.projectId, this.stateTimer.taskId],
                });
                if (this.timesheetId !== timesheetId) {
                    this.timesheetId = timesheetId;
                    await this._get_running_timer();
                }
            } else {
                const seconds = Math.floor(Date.now() / 1000) - this.stateTimer.startSeconds;
                this.timesheetId = await this.rpc({
                    model: 'account.analytic.line',
                    method: 'create',
                    args: [{
                        'name': this.stateTimer.description,
                        'project_id': this.stateTimer.projectId,
                        'task_id': this.stateTimer.taskId,
                    }],
                });
                // Add already runned time and start timer if doesn't running yet in DB
                this.trigger('add_time_timer', {
                    timesheetId: this.timesheetId,
                    time: seconds
                });
            }
            this._match_line();
        }
        async _onClickLineButton(taskId, projectId) {
            // Check that we can create timers for the selected project.
            // This is an edge case in multi-company environment.
            const canStartTimerResult = await this.rpc({
                model: 'project.project',
                method: 'check_can_start_timer',
                args: [[projectId]],
            });
            if (canStartTimerResult !== true) {
                this.trigger('do_action', {action: canStartTimerResult})
                return;
            }
            if (this.stateTimer.addTimeMode === true) {
                this.timesheetId = await this.rpc({
                    model: 'account.analytic.line',
                    method: 'action_add_time_to_timesheet',
                    args: [[this.timesheetId], projectId, taskId, this.props.stepTimer * 60],
                });
                this.trigger('update_timer');
            } else if (! this.timesheetId && this.stateTimer.timerRunning) {
                this.stateTimer.projectId = projectId;
                this.stateTimer.taskId = (taskId) ? taskId : undefined;
                await this._onChangeProjectTaskDebounce(projectId, taskId);
            } else {
                if (this.stateTimer.projectId === projectId && this.stateTimer.taskId === taskId) {
                    await this._stop_timer();
                    return;
                }
                await this._stop_timer();
                this.stateTimer.projectId = projectId;
                this.stateTimer.taskId = (taskId) ? taskId : undefined;
                await this._onTimerStarted();
                await this._onChangeProjectTaskDebounce(projectId, taskId);
            }
            if (this.timerHeader.comp.stopButton.el) {
                this.timerHeader.comp.stopButton.el.focus();
            }
        }
        async _onTimerStarted() {
            this.stateTimer.timerRunning = true;
            this.stateTimer.addTimeMode = false;
            this.stateTimer.startSeconds = Math.floor(Date.now() / 1000);
            if (this.props.defaultProject && ! this.stateTimer.projectId) {
                this.stateTimer.projectId = this.props.defaultProject;
                this._onChangeProjectTaskDebounce(this.props.defaultProject, undefined);
            }
        }
        async _stop_timer() {
            if (!this.timesheetId) {
                this.stateTimer.projectWarning = true;
                return;
            }
            let timesheetId = this.timesheetId;
            this.timesheetId = false;
            this.trigger('stop_timer', {
                timesheetId: timesheetId,
            });
            this.stateTimer.description = '';
            this.stateTimer.timerRunning = false;
            this.timesheetId = false;
            this.stateTimer.projectId = undefined;
            this.stateTimer.taskId = undefined;

            this.stateTimer.timerRunning = false;
            this.stateTimer.projectWarning = false;

            this._match_line();
            this.stateTimer.readOnly = false;
        }
        async _onTimerUnlink() {
            if (this.timesheetId !== false) {
                this.trigger('unlink_timer', {
                    timesheetId: this.timesheetId,
                });
            }
            this.timesheetId = false;
            this.stateTimer.projectId = undefined;
            this.stateTimer.taskId = undefined;

            this.stateTimer.timerRunning = false;
            this.stateTimer.description = '';
            this.stateTimer.manualTimeInput = false;
            this._match_line();
            this.stateTimer.readOnly = false;
            this.stateTimer.projectWarning = false;
        }
        _onNewDescription(data) {
            this.stateTimer.description = data.detail;
            if (this.timesheetId) {
                this.trigger('update_timer_description', {
                    timesheetId: this.timesheetId,
                    description: data.detail
                });
            }
        }
        async _onNewTimerValue(data) {
            const seconds = Math.floor(Date.now() / 1000) - this.stateTimer.startSeconds;
            const toAdd = data.detail * 3600 - seconds;
            this.stateTimer.startSeconds = this.stateTimer.startSeconds - toAdd;
            if (this.timesheetId && typeof toAdd === 'number') {
                this.trigger('add_time_timer', {
                    timesheetId: this.timesheetId,
                    time: toAdd
                });
            }
            this.timerHeader.comp.stopButton.el.focus();
        }

        //----------------------------------------------------------------------
        // Handlers
        //----------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent} ev
         */
        async _onClickStartTimerFromLine(ev) {
            if (! ev.detail) {
                return;
            }
            const cell_path = ev.detail.split('.');
            const grid_path = cell_path.slice(0, -2);
            const row_path = grid_path.concat(['rows'], cell_path.slice(-1));
            const row = utils.into(this.props.data, row_path);
            const data = row.values;
            const task = (data.task_id) ? data.task_id[0] : undefined;
            this._onClickLineButton(task, data.project_id[0]);
        }
        /**
         * @private
         * @param {KeyboardEvent} ev
         */
        async _onKeydown(ev) {
            if (ev.key === 'Shift' && !this.stateTimer.timerRunning && !this.state.editMode) {
                this.stateTimer.addTimeMode = true;
            } else if (!ev.altKey && !ev.ctrlKey && !ev.metaKey && this.showTimerButton && ! ['input', 'textarea'].includes(ev.target.tagName.toLowerCase())) {
                if (ev.key === 'Escape' && this.stateTimer.timerRunning) {
                    this._onTimerUnlink();
                }
                const index = ev.keyCode - 65;
                if (index >= 0 && index <= 26 && index < this.props.data[0].rows.length) {
                    const data = this.props.data[0].rows[index].values;
                    const projectId = data.project_id[0];
                    const taskId = data.task_id && data.task_id[0];
                    this._onClickLineButton(taskId, projectId);
                }
            }
        }
        /**
         * @private
         * @param {KeyboardEvent} ev
         */
        _onKeyup(ev) {
            if (ev.key === 'Shift' && !this.state.editMode) {
                this.stateTimer.addTimeMode = false;
            }
        }
    }

    TimerGridRenderer.props = Object.assign({}, GridRenderer.props, {
        serverTime: {
            type: String,
            optional: true
        },
        stepTimer: {
            type: Number,
            optional: true
        },
        defaultProject: {
            type: [Boolean, Number],
            optional: true
        },
        Component: {
            type: Object,
            optional: true
        },
    });

    TimerGridRenderer.components = {
        TimerHeaderComponent,
        TimerStartComponent,
    };

    return TimerGridRenderer;
});
