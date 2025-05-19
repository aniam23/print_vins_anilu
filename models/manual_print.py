from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import requests
import re

class ManualPrint(models.Model):
    """
    Template for manual printing of trailer data
    Allows you to generate physical labels with technical information
    """
    _name = 'print.manual'
    _description = 'Impresión manual de datos de remolques'
    name = fields.Char(string='Referencia')
    name_trailer = fields.Char(string='Nombre del Remolque')
    model_trailer = fields.Char(string="Modelo del Remolque")
    dry_weight = fields.Float(
        string="Peso Total (LBS)",
        digits=(16, 2),
        help="Ingrese solo valores numéricos con punto decimal (ej: 25.50)."
    )
    gvwr_related = fields.Many2one('vin_generator.gvwr_manager', string='GVWR')
    gawr_related = fields.Many2one('print.gawr', string='GAWR')
    tire_typ = fields.Char(string="Tipo de Llanta")
    model_year = fields.Char(string="Año")
    axles = fields.Char(string="Ejes")
    tongue_type = fields.Char(string="Tipo de Jalon ")
    length = fields.Char(string="Longitud")
    rin = fields.Selection(
        selection=[
            ('ST205/75R15', 'ST205/75R15'),
            ('ST225/75R15', 'ST225/75R15'),
            ('ST235/80R16', 'ST235/80R16'),
            ('ST235/85R16', 'ST235/85R16'),
            ('235235/75R17,5', '235235/75R17,5'),
            ('8235/75R17,5', '8235/75R17,5')
        ],
        string='Rin',
    )
    tire_ply = fields.Selection(
        selection=[
            ('6PLY', '6PLY'),
            ('6PR', '6PR'),
            ('8PLY', '8PLY'),
            ('8PR', '8PR'),
            ('10PLY', '10PLY'),
            ('10PR', '10PR'),
            ('14PLY', '14PLY'),
            ('14PR', '14PR'),
            ('18PLY', '18PLY'),
            ('18PR', '18PR'),
        ],
        string='Capas de Llanta',
    )
    rin_jante = fields.Selection(
        selection=[
            ('15X5', '15X5'),
            ('15X6', '15X6'),
            ('16X6', '16X6'),
            ('17,5X6', '17,5X6'),
        ],
        string='Rin/Jante',
    )
    type_wheel = fields.Selection(
        selection=[
            ('DUAL', 'DUAL'),
            ('SS', 'SS'),
            ('', ''),
        ],
        string='Tipo de llanta',
    )
    vin_registry = fields.Many2one('vin_generator.vin_generator', string='VIN')
    date = fields.Date(string='Fecha', default=fields.Date.today)
    printer_config_id = fields.Many2one(
        'printer.conf', 
        string='Configuración de Impresora',
        domain="[('active', '=', True)]"
    )
   
    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to automatically assign a reference
        when no name is provided.
        :param vals_list: List of dictionaries with the values of the records to be created.
        :return: The records created.
    """
        for vals in vals_list:  # Itera sobre cada diccionario de valores en la lista de registros a crear
            if not vals.get('name'):  # Verifica si el registro actual no tiene especificado un 'name'
        # Asigna un nombre automático usando:
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('manual.print.reference') or 'New'
        #procesa la lista de valores modificada
        return super(ManualPrint, self).create(vals_list)

    def extract_numeric_value(self, value):
        """Extracts the numeric value from a string and returns it as a float
        :param value: String value to extract the numeric value from.
        :return: The numeric value as a float."""

        # Validación de entrada
        if not value or str(value).strip() == '':  
            raise UserError("Error: No se proporcionó ningún valor para extraer el número")

        # Búsqueda de patrones numéricos (incluye decimales correctamente formados)
        matches = re.findall(r'-?\d+\.?\d*', str(value))

        # Validación de resultados
        if not matches:
            raise UserError(f"Error: No se encontró ningún valor numérico válido en: '{value}'")

        # Tomamos el primer match (por si hay varios números en el string)
        numeric_str = matches[0]

        # Validamos que sea un número válido (solo un punto decimal)
        if numeric_str.count('.') > 1:
            raise UserError(f"Error: El valor contiene múltiples puntos decimales: '{numeric_str}'")

        try:
            # Reemplazamos comas por puntos si es necesario (para formato europeo)
            numeric_str = numeric_str.replace(',', '.')
            return float(numeric_str)
        except ValueError:
            raise UserError(f"Error: El valor extraído no es numérico válido: '{numeric_str}'")

    def button_assign_trailer_data(self):
        """Assign all trailer data from product.template"""
        for record in self:
            # busca el modelo de remolque 
            if not record.model_trailer:
                continue  # Salta a la siguiente iteración si no hay modelo de remolque
            product = self.env['product.product'].search([
                ('default_code', '=', record.model_trailer)
            ], limit=1)  # Limita a 1 resultado
            # Si se encontró un producto 
            if product:
                template = product.product_tmpl_id
                # Actualiza los campos del registro con los valores del producto:
                record.update({
                    'name_trailer': product.name,  # Nombre completo del producto
                    'dry_weight': template.dry_weight or 0.0,  # Peso 
                    'gvwr_related': template.gvwr_related.name or '',  # GVWR 
                    'gawr_related': template.gawr_related.name or '',  # GAWR 
                    'tire_typ': template.tire_typ or '',  # Tipo de llanta
                    'model_year': template.model_year or '',  # Año del modelo
                    'axles': template.axles or '',  # Número de ejes
                    'tongue_type': template.tongue_type or '',  # Tipo de jalon
                    'length': template.length or '',  # Longitud del remolque
                })
               

    def get_active_printer(self):
        """Get the active printer from the printer.conf model
           :return: active printer"""
        return self.env['printer.conf'].search([('active', '=', True)], order='sequence', limit=1)

    def send_to_printer_api(self, data):
        """Send data to the printer API
           :param data: JSON data to send printer"""
        #manda llamar a la funcion _prepare_api_data para obtener la impresora y los datos
        printer = self.get_active_printer()
        #si no encuentra impresora activa
        if not printer:
            raise UserError("No hay impresoras activas configuradas")
        #conexion con la impresora
        try:
            response = requests.post(
                f"http://{printer.printer_ip}:{printer.printer_port}/print",
                json=data,
                headers={
                    "Content-Type": "application/json"
                },
                timeout=1000 #tiempo de espera para la conexion con la impresora
            )
            # si la impresora no responde 
            if response.status_code != 200:
                raise UserError(f"Error al imprimir: {response.text}")
        #si la impresora no responde        
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con la impresora: {str(e)}")
    
    def set_tire_ratings(self, specs):
        """Assigns tire specifications based on the rim, tire_ply, and wheel_type fields.
        :param specs: Dictionary where 'tire_rating', 'lbs_wheels', and 'rim' will be assigned
        """
        specs['tire_rating'] = ''
        specs['lbs_wheels'] = ''
        specs['rin'] = self.rin or ''

        # Asegúra que todos los campos requeridos existen
        if not self.rin or not self.tire_ply:
            return
        #convierte a mayusculas y elimina espacios en blanco
        rin = (self.rin or '').strip().upper()
        ply_pr = (self.tire_ply or '').strip().upper()
        tire_type = (self.type_wheel or '').strip().upper()  
        # Obtener el mapa de especificaciones de llantas desde el modelo
        ratings_map = self.env['tire.specifications'].get_ratings_map()

        # Búsqueda exacta
        if rin in ratings_map:
            tire_types = ratings_map[rin]
            # Si no se encontró type_wheel
            if tire_type in tire_types:
                ply_dict = tire_types[tire_type]
                if ply_pr in ply_dict:
                    #agrega los valores a tire_rating y lbs_wheels
                    specs['tire_rating'], specs['lbs_wheels'] = ply_dict[ply_pr]
                    return

        # Búsqueda flexible 
        for available_rin, tire_types in ratings_map.items():
            if available_rin in rin or rin in available_rin:
                # Si no se encontró type_wheel
                if tire_type in tire_types:
                    ply_dict = tire_types[tire_type]
                    if ply_pr in ply_dict:
                        #agrega los valores a tire_rating y lbs_wheels
                        specs['tire_rating'], specs['lbs_wheels'] = ply_dict[ply_pr]
                        return


    def prepare_api_data(self, weight_kg=None):
        """
        Prepare structured data for the printing API.
        :param weight_kg: Weight in kilograms.
        :return: Dictionary of data ready to send to the API.
        """
        # Validar configuración de impresora
        printer = self.get_active_printer()
        # si no encuentra impresora activa
        if not printer:
            raise UserError("¡Error de configuración! No hay impresoras activas")
        # Validar datos de VIN
        if not self.vin_registry:
            raise UserError("¡Dato faltante! Asigne un VIN antes de imprimir")

        # Validar peso en libras
        weight_lb = self.dry_weight or 0
        # no permite que el peso sea 0
        if weight_lb <= 0:
            raise UserError("¡Dato inválido! El peso total (dry_weight) no puede ser 0")
        #busca los datos de GVWR y GAWR
        try:
            gvwr_lb = self.extract_numeric_value(self.gvwr_related)
            gawr_lb = self.extract_numeric_value(self.gawr_related)
            #no permite que el GVWR y GAWR sean 0
            if gvwr_lb <= 0:
                raise UserError("¡Dato inválido! El GVWR debe ser mayor que 0")
            if gawr_lb <= 0:
                raise UserError("¡Dato inválido! El GAWR debe ser mayor que 0")

        except UserError as e:
            raise UserError(f"Error en datos técnicos: {str(e)}")

        # Conversión a kilogramos
        weight_kg = int(weight_lb * 0.453592) if weight_kg is None else weight_kg
        gvwr_kg = int(gvwr_lb * 0.453592)
        gawr_kg = int(gawr_lb * 0.453592)

        # Obtener especificaciones de llantas
        tire_specs = {
            'tire_rating': '',
            'lbs_wheels': '',
            'rim': '',
            'rim_jante': self.rin_jante or ''
        }
        #manda llamar la funcion set_tire_ratings para obtener los datos de tire_ratings y lbs_wheels y rin_jante
        self.set_tire_ratings(tire_specs)

        # Preparar datos para la API
        return {
            "ip": printer.printer_ip,
            "port": printer.printer_port,
            "weight_lb": weight_lb,
            "weight_kg": weight_kg,
            "gvwr_lb": gvwr_lb,
            "gvwr_kg": gvwr_kg,
            "gawr_lb": gawr_lb,
            "gawr_kg": gawr_kg,
            "tire_rating": tire_specs['tire_rating'],
            "lbs_wheels": tire_specs['lbs_wheels'],
            "rim": tire_specs['rin'],
            "rim_jante": tire_specs['rim_jante'],
            "product_vin": self.vin_registry.vin,
            "model_string": self.model_trailer or "",
            "fecha_impresion": self.date.strftime('%m/%Y') if self.date else datetime.now().strftime('%m/%Y')
        }

    def print_manual_vins(self):
        """Main action for printing manual labels
        :return: confirmation of label send"""
        # solo permite imprimir una etiqueta a la ves
        self.ensure_one()
        # manda llamar la funcion prepare_api_data para obtener los datos de la etiqueta
        print_data = self.prepare_api_data()
        self.send_to_printer_api(print_data)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'La etiqueta se ha enviado a la impresora',
                'type': 'success',
                'sticky': False,
            }
        }

