# -*- coding: utf-8 -*-
import datetime
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError
from openerp import api, fields, models

class WebsiteSupportSLA(models.Model):

    _name = "website.supportzayd.sla"

    name = fields.Char(string="Name", translate=True)
    description = fields.Text(string="Description", translate=True)
    sla_duration = fields.Float(string='SLA Solve Time',required = True)
    rule_ids = fields.One2many('website.supportzayd.sla.rule', 'vsa_id', string="Rules", help="If a ticket matches mutiple rules then the one with the lowest response time is used")
    response_time_ids = fields.One2many('website.supportzayd.sla.response', 'vsa_id', string="(DEPRICATED) Category Response Times (Working Hours)")
    alert_ids = fields.One2many('website.supportzayd.sla.alert', 'vsa_id', string="Email Alerts")

class WebsiteSupportSLARule(models.Model):

    _name = "website.supportzayd.sla.rule"
    _order = "response_time asc"

    vsa_id = fields.Many2one('website.supportzayd.sla', string="SLA")
    name = fields.Char(string="Name", required="True")
    condition_ids = fields.One2many('website.supportzayd.sla.rule.condition', 'wssr_id', string="Conditions", help="All conditions have to be fulfilled for the rule to apply, e.g. priority='High' AND category='Tech Support'", required="True")
    response_time = fields.Float(string="Response Time", required="True", help="If the support ticket matches the conditions then it has to be completed within this amount of time, e.g. high priority tech support ticket within 1 hour")
    countdown_condition = fields.Selection([('business_only','Business Only'), ('24_hour','24 Hours')], default="24_hour", required="True", help="During what time do we start counting down the SLA timer")

class WebsiteSupportSLARuleCondition(models.Model):

    _name = "website.supportzayd.sla.rule.condition"

    wssr_id = fields.Many2one('website.supportzayd.sla.rule', string="SLA Rule")
    type = fields.Selection([('category','Category'), ('subcategory','Sub Category'), ('priority','Priority')], string="Type", required="True")
    display_value = fields.Char(string="Display Value", compute="_compute_display_value")
    category_id = fields.Many2one('website.supportzayd.ticket.categories', string="Category")
    subcategory_id = fields.Many2one('website.supportzayd.ticket.subcategory', string="Sub Category")
    #priority_id = fields.Many2one('website.supportzayd.ticket.priority', string="Priority")

    #@api.one
    #@api.depends('type','category_id','subcategory_id','priority_id')
    #def _compute_display_value(self):
    #    if self.type == "category":
    #        self.display_value = self.category_id.name
    #    elif self.type == "subcategory":
    #        self.display_value = self.subcategory_id.name
    #    elif self.type == "priority":
    #        self.display_value = self.priority_id.name
        
class WebsiteSupportSLAResponse(models.Model):

    _name = "website.supportzayd.sla.response"

    vsa_id = fields.Many2one('website.supportzayd.sla', string="SLA")
    category_id = fields.Many2one('website.supportzayd.ticket.categories', string="Ticket Category", required="True")
    response_time = fields.Float(string="Response Time", required="True")
    countdown_condition = fields.Selection([('business_only','Business Only'), ('24_hour','24 Hours')], default="24_hour", required="True")
    partner_ids = fields.Many2many('res.partner', string="Customers", help="SLA policies will apply to any customers selected. "
                                                                         "Pleave leave it empty to apply to all customers")


    @api.multi
    def name_get(self):
        res = []
        for sla_response in self:
            name = sla_response.category_id.name + " (" + str(sla_response.response_time) + ")"
            res.append((sla_response, name))
        return res

    @api.model
    def create(self, values):
    
        #Can not have multiple of the same category on a single SLA
        if self.env['website.supportzayd.sla.response'].search_count([('vsa_id','=', values['vsa_id']), ('category_id','=', values['category_id'])]) > 0:
           raise UserError("You can not use the same category twice")
    
        #Setting for business hours has to be set before they can use business hours only SLA option
        if values['countdown_condition'] == 'business_only':
            setting_business_hours_id = self.env['ir.default'].get('website.supportzayd.settings', 'business_hours_id')
            if setting_business_hours_id is None:
                raise UserError("Please set business hours in settings before using this option")

        return super(WebsiteSupportSLAResponse, self).create(values)
        
class WebsiteSupportSLAAlert(models.Model):

    _name = "website.supportzayd.sla.alert"
    _order = "alert_time desc"

    vsa_id = fields.Many2one('website.supportzayd.sla', string="SLA")
    alert_time = fields.Float(string="Alert Time", help="Number of hours before or after SLA expiry to send alert")
    type = fields.Selection([('email','Email')], default="email", string="Type")