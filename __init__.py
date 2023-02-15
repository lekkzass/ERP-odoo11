# -*- coding: utf-8 -*-
from . import models
from . import controllers
from odoo import api, SUPERUSER_ID

def _unlink_messages_data(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})
	#messages = env["mail.message"].search([]).unlink() 
	env['website.supportzayd.ticket'].unlink_on_uninstall()
