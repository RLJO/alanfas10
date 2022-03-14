# -*- coding: utf-8 -*-

from odoo import models, fields, api,_,tools
#from speechd_config.config import report
import datetime



class Faccounbttmoveswizrad(models.TransientModel):
    _name= 'f.accounbt.moves.wizard' 
    _description = "Account Report Wizard"
   
   
    from_date = fields.Date("From ",required=True)
    to_date = fields.Date("To",required=True)
    
    
    def _intialselect(self):
        return """
        
        select
        id,
        customer_pay,
        vendor_pay,
        inv_bill_amount,
        currency_id,
        type,
        ref,
        partner_id,
        note,
        date
        
        """
        
        
        
    def _payselect(self):
        return """
        
      
        SELECT 
        
        pay.id as id,
        case when (pay.payment_type = 'inbound' ) then pay.amount else 0 end  as customer_pay,
        case when (pay.payment_type = 'outbound' ) then pay.amount else 0 end  as vendor_pay,
        0 as inv_bill_amount,
        pay.currency_id as currency_id,
        case pay.payment_type
        when 'inbound' then 'مقبوضات'
        when 'outbound' then 'مدفوعات'
        else ''
        end as type,
     
        am.name as ref,
        pay.partner_id as partner_id,
        '' as note,
        am.date as date
        
        """
        
        
    def _payfrom(self):
        return """  
         FROM 
         
         account_payment pay
         left join account_move am on (pay.move_id = am.id)
                      
   
                
         
         
         """
         
    def _paywhere(self):
        return """
        
        where 
        am.state = 'posted'
                and   pay.payment_type  IN ('inbound','outbound') 
                and  date(am.date) >= date('%s') and date(am.date) <= date('%s') 
        """%(self.from_date,self.to_date) 
        
        
    def _Invselect(self):
        return """
        
        select
        COALESCE((Select max (id) from account_payment),0)   + inv.id as id ,
        0 as customer_pay,
        0  as vendor_pay,
        case when (inv.move_type in ( 'out_invoice','in_refund') ) then inv.amount_total else inv.amount_total*-1  end  as inv_bill_amount,
        inv.currency_id as currency_id,
        case inv.move_type
        when 'out_invoice' then 'فواتير زبائن'
        when 'out_refund' then 'مردودات زبائن'
        when 'in_invoice' then 'فواتير موردين'
        when 'in_refund' then 'مردودات موردين'
        else ''
        end as type,
     
       inv.name as ref,
        inv.partner_id as partner_id,
        '' as note,
        inv.invoice_date as date
        
        """
        
        
    def _invfrom(self):
        return """  
         FROM 
         
         account_move inv
         
         
         """
         
         
    def _invwhere(self):
        return """
        
        where 
         inv.state = 'posted'
                and   inv.move_type  IN ('out_invoice','out_refund','in_invoice','in_refund')
                 and 
        inv.invoice_date >= ('%s') and inv.invoice_date <= ('%s') 
        """%(self.from_date,self.to_date) 
        
        
        
    def get_moves_accounts_details(self):
        print("55555555555555555")
        
        tools.drop_view_if_exists(self.env.cr, 'f_account_details_moves')
        
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW f_account_details_moves AS (
        %s
       
                FROM
              (
               ( %s
                 %s
                 %s)
              Union all
                ( %s
                %s
              %s
               )
               
               )prod
              
           
         )
        
         """ % (self._intialselect(),self._payselect(),self._payfrom(),self._paywhere(),
                self._Invselect(),self._invfrom(),self._invwhere()))
        
        
       
       
        tree_id = self.env.ref('iq_custom_account_report.view_report_accountproductsmoves_tree').id  

        action = {
            'name':_('Accounting Details  Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'f.account.details.moves',
            
            }
        
        return action
        
        
        