from odoo import models, fields, _, api 
from odoo.exceptions import ValidationError
import requests
import json

class Weather(models.Model):
    _inherit = 'event.event'
    
    long = fields.Char('Longitude')
    lat = fields.Char('Latitude')
    weather = fields.Selection([
        ('sunny', 'Sunny'),
        ('windy', 'Windy'),
        ('cloudy', 'Cloudy'),
        ('rainy', 'Rainy'),
    ])

    def get_weather(self):
        partner = self.address_id
        result = partner._geo_localize(partner.street,
                                        partner.zip,
                                        partner.city,
                                        partner.state_id.name,
                                        partner.country_id.name)
        latitude = result[0]
        longitude = result[1]
        
        api_key = 41eae7153956aa5aa0501ee9681bfdec
        
        api_url = "https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"
        api_response = requests.get(api_url)
        response_content = api_response.content
        response_object = json.loads(response_content)
        # api_weather = response_object.weather.main
        raise ValidationError(str(response_object))
        
        self.write({
            'lat':api_weather,
            'long':api_weather,
        })
        
        

