# import requests
# from python_ipware import IpWare
# from ua_parser.user_agent_parser import Parse
#
#
# def login_device_info(request=None):
#     device = get_device(request=request)
#     ip, location = get_ip_location(request=request)
#     return {
#         'ip_address': ip.exploded,
#         'device': device,
#         'location': location
#     }
#
# def get_device(request:None):
#     a = Parse(request.user_agent.string)
#     agent = a.get('user_agent').get('family')
#     os = a.get('os').get('family')
#     return f'{agent} - {os}'
#
# def get_ip_location(request:None):
#     ipw = IpWare()
#     meta = request.environ
#     ip, trusted_route = ipw.get_client_ip(meta=meta)
#
#     if ip:
#         try:
#             url = "https://api.ip2location.io/?key=644936F8491E78D034A6E8035D950557&ip=102.89.23.169"
#             re = requests.get(url=url).json()
#             __city = re.get('city_name')
#             __country = re.get('country_name')
#             return (ip, f"{__city}, {__country}")
#         except Exception as e:
#             return (ip, '')
#
