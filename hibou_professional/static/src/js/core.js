odoo.define('hibou_professional.core', function (require) {
"use strict";

var Widget = require('web.Widget');
var SystrayMenu = require('web.SystrayMenu');

var HibouProfessionalSystrayWidget = Widget.extend({
    template: 'HibouProfessionalSystrayWidget',

    start: function() {
        var self = this;
        self.expiration_date = false;
        self.expiration_reason = false;
        self.professional_code = false;
        this.types = [['lead', 'Sales'], ['ticket', 'Support']];
        this.message_subjects = {'lead': [], 'ticket': [], 'task': []};
        self.expiring = false;
        self.expired = false;
        self.dbuuid = false;
        self.quote_url = false;
        self.is_admin = false;
        self.allow_admin_message = false;
        self.allow_message = false;
        this._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_status',
        }).then(function (result) {
            self.handleStatusUpdate(result);
        });
        return this._super();
    },

    get_subjects: function(type) {
        if (this.message_subjects && this.message_subjects[type]) {
            return this.message_subjects[type]
        }
        return [];
    },

    set_error: function(error) {
        this.$('.hibou_professional_error').text(error);
    },

    update_message_type: function(el) {
        var selected_type = this.$('select.hibou_message_type').val();
        if (selected_type && this.$('.hibou_subject_selection_option.' + selected_type).length > 0) {
            this.$('#hibou_subject_selection').show();
            this.$('.hibou_subject_selection_option').hide().attr('disabled', true);
            this.$('.hibou_subject_selection_option.' + selected_type).show().attr('disabled', false);
            var selected_subject = this.$('.hibou_subject_selection_option.' + selected_type)[0];
            this.$('select.hibou_subject_selection').val(selected_subject.value);
        } else if (selected_type) {
            this.$('select.hibou_subject_selection').val('0');
            this.$('#hibou_subject_selection').hide();
        } else {
            this.$('#hibou_subject_selection').hide();
            this.$('#hibou_message_priority').hide();
            this.$('#hibou_message_subject').hide();
        }
        this.update_subject_selection();
    },

    update_subject_selection: function(el) {
        var selected_subject = this.$('select.hibou_subject_selection').val();
        if (selected_subject == '0') {
            this.$('#hibou_message_priority').show();
            this.$('#hibou_message_subject').show();
        } else {
            this.$('#hibou_message_priority').hide();
            this.$('#hibou_message_subject').hide();
        }
    },

    update_message_subjects: function(subjects_by_type) {
        // TODO actually update instead of overriding...
        this.message_subjects = subjects_by_type;
        this.renderElement();
    },

    button_update_subscription: function() {
        var self = this;
        var professional_code = self.$('input.hibou_professional_code').val();
        if (!professional_code) {
            alert('Please enter a subscription code first.');
            return;
        }
        self.$('.update_subscription').prop('disabled', 'disabled');
        self._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_update',
            args: [professional_code],
        }).then(function (result) {
            self.$('.update_subscription').prop('disabled', false);
            self.handleStatusUpdate(result);
        });
    },

    button_update_message_preferences: function() {
        var self = this;
        var allow_admin_message = self.$('input.hibou_allow_admin_message').prop('checked');
        var allow_message = self.$('input.hibou_allow_message').prop('checked');
        self.$('.update_message_preferences').prop('disabled', 'disabled');
        self._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_update_message_preferences',
            args: [allow_admin_message, allow_message],
        }).then(function (result) {
            self.$('.update_message_preferences').prop('disabled', false);
            self.handleStatusUpdate(result);
        });
    },

    button_quote: function() {
        var self = this;
        var message_p = self.$('.button-quote-link p');
        message_p.text('Retrieving URL...');
        self._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_quote',
        }).then(function (result) {
            if (result && result['url']) {
                self.quote_url = result.url
                self.$('.button-quote-link').attr('href', self.quote_url);
                message_p.text('Quote URL ready. Click again!');
            } else {
                message_p.text('Error with quote url.  Maybe the database token is incorrect.');
            }
        });
    },

    button_send_message: function() {
        var self = this;
        var message_type = self.$('select.hibou_message_type').val();
        var message_priority = self.$('select.hibou_message_priority').val();
        var message_subject = self.$('input.hibou_message_subject').val();
        var message_subject_id = self.$('select.hibou_subject_selection').val();
        var current_url = window.location.href;
        if (message_subject_id == '0' && (!message_subject || message_subject.length < 3)) {
            alert('Please enter a longer subject.');
            return;
        }
        var message_body = self.$('textarea.hibou_message_body').val();
        self.$('.hibou_send_message').prop('disabled', 'disabled');
        self._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_send_message',
            args: [message_type, message_priority, message_subject, message_body, current_url, message_subject_id],
        }).then(function (result) {
            // TODO result will have a subject to add to the subjects and re-render.
            self.$('.hibou_send_message').prop('disabled', false);
            var message_response = self.$('.hibou_message_response');
            var access_link = self.$('.hibou_message_response a');
            var message_form = self.$('.hibou_message_form');
            if (!result) {
                access_link.text('An error has occured.')
            } else {
                if (result.error) {
                    access_link.text(result.error);
                } else {
                    access_link.text(result.message || 'Your message has been received.')
                }
                if (result.access_url) {
                access_link.attr('href', result.access_url);
                }
            }
            message_response.show();
            message_form.hide();
        });
    },

    button_get_messages: function() {
        var self = this;
        var $button = this.$('.hibou_get_messages');
        $button.prop('disabled', 'disabled');
        self._rpc({
            model: 'publisher_warranty.contract',
            method: 'hibou_professional_get_messages',
            args: [],
        }).then(function (result) {
            $button.prop('disabled', false);
            if (result['message_subjects']) {
                self.update_message_subjects(result.message_subjects);
                setTimeout(function () {
                    self.$('.dropdown-toggle').click();
                }, 100);
            } else if (result['error']) {
                self.set_error(result['error']);
            }
        });
    },

    renderElement: function() {
        var self = this;
        this._super();

        this.update_message_type();
        this.update_subject_selection();

        this.$('select.hibou_message_type').on('change', function(el) {
            self.update_message_type(el);
        });
        this.$('select.hibou_subject_selection').on('change', function(el) {
            self.update_subject_selection(el);
        });

        // Update Subscription Button
        this.$('.update_subscription').on('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            self.button_update_subscription();
        });

        this.$('.hibou_get_messages').on('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            self.button_get_messages();
        });

        // Retrieve quote URL
        this.$('.button-quote-link').on('click', function(e){
            if (self.quote_url) {
                return;  // allow default url click event
            }
            e.preventDefault();
            e.stopPropagation();
            self.button_quote();
        });

        // Update Message Preferences Button
        this.$('.update_message_preferences').on('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            self.button_update_message_preferences();
        });

        // Send Message Button
        this.$('.hibou_send_message').on('click', function(e){
            e.preventDefault();
            e.stopPropagation();
            self.button_send_message();
        });

        // Kill the default click event
        this.$('.hibou_message_form_container').on('click', function (e) {
            //e.preventDefault();
            e.stopPropagation();
        })
    },

    handleStatusUpdate: function(status) {
        this.expiration_date = status.expiration_date;
        this.expiration_reason = status.expiration_reason;
        this.professional_code = status.professional_code;
        this.types = [['lead', 'Sales'], ['ticket', 'Support']];
        if (this.professional_code) {
            this.types.push(['task', 'Project Manager/Developer'])
        }
        this.expiring = status.expiring;
        this.expired = status.expired;
        this.dbuuid = status.dbuuid;
        this.is_admin = status.is_admin;
        this.allow_admin_message = status.allow_admin_message;
        this.allow_message = status.allow_message;
        this.renderElement();
    },

});

SystrayMenu.Items.push(HibouProfessionalSystrayWidget);

return {
    HibouProfessionalSystrayWidget: HibouProfessionalSystrayWidget,
};

});