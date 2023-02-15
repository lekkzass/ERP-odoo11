# -*- coding: utf-8 -*-
import datetime
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError
from openerp import api, fields, models

AVAILABLE_PRIORITIES = [
    ('0', 'Neutral'),
    ('1', 'Low'),
    ('2', 'High Priority'),
    ('3', 'Urgent'),
]
class WebsiteSupportSLAPolicies(models.Model):
    #this is a test function created because the current SLA is a bit confusing with the business process. @hafizalwi13jan
    _name = "website.supportzayd.sla.policies"

    name = fields.Char(string="Name", translate=True)
    description = fields.Text(string="Description", translate=True)

    #below are things for email alert
    #vsa_id = fields.Many2one('website.supportzayd.sla.', string="SLA") #i am not sure what is this, but it is included in the original module, and is needed for the alert_time email to be triggered
    alert_time = fields.Float(string="Alert Time", help="Number of hours before or after SLA expiry to send alert")


    #below is our criteria for the SLA Policies to be triggered
    category_id = fields.Many2one('website.supportzayd.ticket.categories', string="Category", help="Select which category to apply SLA,leave empty to apply to all categories")
    minimum_priority = fields.Selection(AVAILABLE_PRIORITIES, index=True)
    partner_ids = fields.Many2many ('res.partner', string="Customers", help="select applicable for which customers, leave empty to select all customers")

    #below is our "target & email alert" for the SLA policies if triggered
    #sla_duration = fields.Float(string='SLA Total Allocated Time', required=True) #note that this is the total allocated SLA time
    countdown_condition = fields.Selection([('business_only', 'Business Only'), ('24_hour', '24 Hours')],
                                           default="24_hour", required="True")

    SLA_helpdesk_response_time = fields.Float(string="SLA Helpdesk response time: " , help="Onsite timer is duration from open case to create date")
    SLA_onsite_response_time = fields.Float(string="SLA On-Site response time: ", help="Onsite timer is duration from create date to checkin")
    SLA_resolution_response_time = fields.Float(string="SLA Problem resolution response time: ", help="Resolution timer is duration from checkin to checkout")
    SLA_tot_allocated = fields.Float(string='SLA Total Allocated Time', compute="get_total_allocated_SLA")  # note this is the total of SLA1 aka helpdeskresponse(if exist) + SLA2 aka onsiteResponse + SLA3 aka problem resoluton time
    countdown_condition = fields.Selection([('business_only', 'Business Only'), ('24_hour', '24 Hours')],
                                           default="24_hour", required="True")

    #alert_ids = fields.One2many('website.supportzayd.sla.policies', 'vsa_id', string="Email Alerts"
    @api.one
    def get_total_allocated_SLA(self):
        total=self.SLA_resolution_response_time #let say this is 1
        if self.SLA_helpdesk_response_time: #let say this is 2
            total = total + self.SLA_helpdesk_response_time

        if self.SLA_onsite_response_time: # this is 3, let say
            total = total + self.SLA_onsite_response_time
        self.SLA_tot_allocated = total




    """ sla_timer_helpdesk_response_time = create_date(field.Datetime) - open case
            sla_timer_site_response_time_start = create_date
        sla_timer_site_response_time = check_in(field.Datetime) - sla_timer_site_response_time_start 
            sla_timer_resolution_time_start = check_in
        sla_timer_resolution_time = date.now - sla_timer_resolution_time_start """











