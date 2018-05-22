# -*- coding: utf-8 -*-

from odoo import http, tools
import odoo.addons.bus.controllers.main

try:
    import newrelic
    import newrelic.agent
except ImportError:
    newrelic = None


class BusController(odoo.addons.bus.controllers.main.BusController):

    @http.route()
    def send(self, channel, message):
        if newrelic:
            newrelic.agent.ignore_transaction()
        return super(BusController, self).send(channel, message)

    @http.route()
    def poll(self, channels, last, options=None):
        if newrelic:
            newrelic.agent.ignore_transaction()
        return super(BusController, self).poll(channels, last, options)

try:
    if tools.config['debug_mode']:
        class TestErrors(http.Controller):
            @http.route('/test_errors_404', auth='public')
            def test_errors_404(self):
                import werkzeug
                return werkzeug.exceptions.NotFound('Successful test of 404')

            @http.route('/test_errors_500', auth='public')
            def test_errors_500(self):
                raise ValueError
except KeyError:
    pass
