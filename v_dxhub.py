#
# project: sPAD
#
# dxhub client
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import requests


class Dxhub():
    def __init__(self, service, parameter):
        self.service = service
        self.parameter = parameter
        self.api_url = self.create_api_url()

    def create_api_url(self):
        base_url = "http://127.0.0.1/service.php?"
        api_key = "demo"
        sid = "requestid=eefka&serviceid=validator"
        if self.service == "AMKA2DATA":
            sid = ""
        api_url = f"{base_url}apikey={api_key}&tag={self.service}&{sid}&{self.parameter}="
        return api_url

    def service_call(self, value):
        try:
            response = requests.get(self.api_url + value)
            return response.status_code, response.json()
        except Exception as e:
            return 999, f"{'error':'{e}'}"
    
