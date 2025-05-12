from odoo import models, fields, api
from odoo.exceptions import UserError

class PrinterConfig(models.Model):
    """
    Template for configuring printers in the system
    Stores connection settings for physical or virtual printers
    with the ability to prioritize by sequence.
    """
    _name = 'printer.conf' 
    _description = 'Configuración de Impresora'  
    _order = 'sequence, id'  
    name = fields.Char(string='Nombre', required=True)  
    printer_ip = fields.Char(string='IP de la Impresora', required=True) 
    printer_port = fields.Integer(string='Puerto', default=6000)  
    active = fields.Boolean(string='Activo', default=True) 
    sequence = fields.Integer(string='Prioridad', default=10)  
    # Campo calculado para la URL completa de la API
    printer_api_url = fields.Char(
        string='URL de la API', 
        compute='_compute_api_url',  
        store=True  
    )
    
    @api.depends('printer_ip', 'printer_port')  # Se recalcula cuando cambian estos campos
    def _compute_api_url(self):
        """
        Method that constructs the full URL of the print API
        Format: http://[ip]:[port]/print
        """
        for record in self:
            # Construye la URL concatenando los valores
            record.printer_api_url = f"http://{record.printer_ip}:{record.printer_port}/print"

    