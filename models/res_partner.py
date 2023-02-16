# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResPartnerTicket(models.Model):

    _inherit = "res.partner"

    support_ticket_ids = fields.One2many('website.supportzayd.ticket', 'partner_id', string="Tickets")
    support_ticket_count = fields.Integer(compute="_count_support_tickets", string="Ticket Count")
    new_support_ticket_count = fields.Integer(compute="_count_new_support_tickets", string="New Ticket Count")
    support_ticket_string = fields.Char(compute="_compute_support_ticket_string", string="Support Ticket String")
    stp_ids = fields.Many2many('res.partner', 'stp_res_partner_rel', 'stp_p1_id', 'stp_p2_id', string="Support Ticket Access Accounts", help="(DEPRICATED use departments) Can view support tickets from other contacts")
    sla_policies_id = fields.Many2one('website.supportzayd.sla.policies', string="SLA")
    dedicated_support_user_id = fields.Many2one('res.users', string="Dedicated Support User")
    ticket_default_email_cc = fields.Char(string="Default Email CC")
    ticket_default_email_body = fields.Text(string="Default Email Body")

    @api.model
    def create_support_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'website.supportzayd.ticket',
            'view_mode': 'form',
            'context': {'default_partner_id': self.id},
            'target': 'new',
        }

    @api.model
    @api.depends('support_ticket_ids')
    def _count_support_tickets(self):
        for record in self:
            record.support_ticket_count = record.support_ticket_ids.sudo().search_count([('partner_id','=',record.id)])

    @api.model
    @api.depends('support_ticket_ids')
    def _count_new_support_tickets(self):
        """Sets the amount of new support tickets owned by this customer"""
        opened_state = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_open')
        for record in self:
            record.new_support_ticket_count = record.support_ticket_ids.sudo().search_count(
                [('partner_id', '=', record.id), ('state', '=', opened_state.id)])

    @api.model
    @api.depends('support_ticket_count', 'new_support_ticket_count')
    def _compute_support_ticket_string(self):
        for record in self:
            record.support_ticket_string = str(record.support_ticket_count) + " (" + str(record.new_support_ticket_count) + ")"
