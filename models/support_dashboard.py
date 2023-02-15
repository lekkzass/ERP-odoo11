# -*- coding: utf-8 -*-
from odoo import fields, models


# class View is absolutely necessary, class ActWindowView is optional but its a good idea, Used when specifying views
# very explicitly via view_ids please read documentation to understand more

class View(models.Model):
    _inherit = 'ir.ui.view'
    type = fields.Selection(
        selection_add=[('supportdashboard', "SupportDashboard")])



class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'
    view_mode = fields.Selection(
        selection_add=[('supportdashboard', "SupportDashboard")])

