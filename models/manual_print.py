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
    wheel = fields.Char(string="Llanta")
    dry_weight = fields.Float(string="Peso Total (LBS)")
    gvwr_related = fields.Char(string="GVWR")
    gawr_related = fields.Char(string="GAWR")
    tire_typ = fields.Char(string="Tipo de Llanta")
    model_year = fields.Char(string="Año")
    axles = fields.Char(string="Ejes")
    tongue_type = fields.Char(string="Tipo de Jalon ")
    length = fields.Char(string="Longitud")
    rin_jante = fields.Char(string="Rin/Jante")
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
        # Búsqueda de patrones numéricos (incluye decimales y comas)
        numbers = re.findall(r'[\d,\.]+', str(value))
        # Validación de resultados
        if not numbers:
            raise UserError(f"Error: No se encontró ningún valor numérico en: '{value}'")
        # Limpieza y conversión del valor
        try:
            numeric_value = numbers[0].replace(',', '')  
            return float(numeric_value)
        except ValueError:
            raise UserError(f"Error: El valor extraído no es numérico válido: '{numbers[0]}'")

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
                # Busca la lista de materiales del producto
                bom = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', template.id)  
                ], limit=1)  
                # Si existe una lista de materiales 
                if bom:
                    # Filtra las líneas del BOM para encontrar componentes de llantas
                    wheels = bom.bom_line_ids.filtered(
                        lambda l: 'llanta' in l.product_id.name.lower()  # Busca 'llanta' en el nombre
                    )
                    # Asigna el nombre de la primera llanta encontrada (o cadena vacía si no hay)
                    record.wheel = wheels[0].product_id.name if wheels else ''

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
        """Assigns technical specifications based on the rim (wheel field)
            :param specs: Dictionary to store the tire ratings
        """
        # inicializa las variables de especificaciones de llantas
        specs['tire_rating'] 
        specs['lbs_wheels'] 
        specs['rin'] = ''
        # si no encuentra el campo wheel
        if not self.wheel:
            return # Evita seguir buscando innecesariamente cuando ya encontramos el campo.
        #si encuentra el campo wheel lo divide en partes para obtener informacion especifica  de la llanta
        wheel_info = self.wheel.upper().split()
        # Extrae el rin y el tipo de ply de la información de la llanta
        if 'LLANTA' in wheel_info:
            llanta_index = wheel_info.index('LLANTA')
            if llanta_index + 1 < len(wheel_info):
                specs['rin'] = wheel_info[llanta_index + 1]
                ply_match = wheel_info[llanta_index + 2]
        # Determina el tipo de llanta 
        tire_type = 'DUAL' if 'DUAL' in wheel_info else 'SS' if 'SS' in wheel_info else ''
        # si no encuentra el tipo de llanta
        if not ply_match:
            return # Evita seguir buscando innecesariamente cuando ya encontramos el campo
        #manda llamar las variables de rin y ply de la llanta
        ply_pr = ply_match
        rin = specs['rin']

        # busca coincidencias en el modelo tire.specifications  basadose en el rin, el tipo de llanta y el ply
        ratings_map = self.env['tire.specifications'].get_ratings_map()

        # si encuentra exactamente el rin, el tipo de llanta y el ply
        if rin in ratings_map:
            if tire_type in ratings_map[rin]:
                if ply_pr in ratings_map[rin][tire_type]:
                    specs['tire_rating'], specs['lbs_wheels'] = ratings_map[rin][tire_type][ply_pr] #agrega los valores de tire_rating y lbs_wheels
                    return #Asegura que el método termine justo después de encontrar la coincidencia más específica

        
       # Itera sobre todos los rin disponibles en el mapa de especificaciones
        for available_rin in ratings_map:
            # Compara si el rin actual coincide total o parcialmente con el rin buscado
            if available_rin in rin or rin in available_rin:
                # Verifica si el tipo de llanta (DUAL/SS) existe para este rin
                if tire_type in ratings_map[available_rin]:
                    # Busca si el ply/PR específico existe para este tipo de llanta
                    if ply_pr in ratings_map[available_rin][tire_type]:
                        # Asigna los valores encontrados a las variables de especificaciones de llantas
                        specs['tire_rating'], specs['lbs_wheels'] = ratings_map[available_rin][tire_type][ply_pr]
                        # Termina la función inmediatamente al encontrar la primera coincidencia válida
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
