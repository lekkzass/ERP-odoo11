# -*- coding: utf-8 -*-
from odoo import api, fields, models


# class View is absolutely necessary, class ActWindowView is optional but its a good idea, Used when specifying views
# very explicitly via view_ids please read documentation to understand more

class View(models.Model):
    _inherit = 'ir.ui.view'

    #TODO please check this code. set null should be set default. but if set to setdefault error will occur which is cannot find the defaut. hafizalwi13feb2023
    type = fields.Selection(
        selection_add=[('supportdashboard', "SupportDashboard")], ondelete={'supportdashboard': 'cascade'}

    )



class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    #TODO please check this code. set null should be set default. but if set to setdefault error will occur which is cannot find the defaut. hafizalwi13feb2023
    view_mode = fields.Selection(
        selection_add=[('supportdashboard', "SupportDashboard")], ondelete={'supportdashboard': 'cascade'})

