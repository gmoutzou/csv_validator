#
# project: sPAD
#
# dxhub client
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import requests


class Dxhub():
    def __init__(self, service, param_name):
        self.service = service
        self.param_name = param_name
        self.api_url = f""
    
    def service_call(self, param_value):
        try:
            response = requests.get(self.api_url + param_value)
            return response.status_code, response.json()
        except Exception as e:
            return 999, f"{'error':'{e}'}"


def main():
    dxhub = Dxhub('IDENTITY', 'afm')
    print(dxhub.service_call('999999999'))

if __name__ == "__main__":
    main()
    
