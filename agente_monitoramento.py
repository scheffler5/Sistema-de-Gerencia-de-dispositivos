import psutil
import requests
import time
import json
from uuid import getnode as get_mac # Para obter o MAC Address

# --- CONFIGURAÇÕES ---
# O endereço da sua API Django (ajuste o IP e a porta se necessário)
URL_DO_SERVIDOR = "http://127.0.0.1:8000/app/api/receive_monitoring/"
# Intervalo em segundos para enviar os dados
INTERVALO = 60 # 60 segundos = 1 minuto

def obter_mac_address():
    """ Obtém o endereço MAC da máquina como identificador único. """
    mac = get_mac()
    return ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

def coletar_dados():
    """ Coleta as métricas de hardware usando psutil. """
    dados = {
        'mac_address': obter_mac_address(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        # Pega o uso do disco principal (ex: C: no Windows)
        'disk_percent': psutil.disk_usage('/').percent, 
    }
    return dados

def enviar_dados(dados):
    """ Envia os dados coletados para o servidor Django. """
    try:
        # Usamos um header para indicar que estamos a enviar JSON
        headers = {'Content-Type': 'application/json'}
        # requests.post envia os dados via método POST
        response = requests.post(URL_DO_SERVIDOR, data=json.dumps(dados), headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"[{time.ctime()}] Dados enviados com sucesso!")
        else:
            print(f"[{time.ctime()}] Erro ao enviar dados. Servidor respondeu com status {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] Falha na conexão com o servidor: {e}")

if __name__ == "__main__":
    print("--- Agente de Monitoramento Iniciado ---")
    print(f"Enviando dados para: {URL_DO_SERVIDOR}")
    print(f"Identificador da máquina (MAC): {obter_mac_address()}")
    while True:
        dados_coletados = coletar_dados()
        enviar_dados(dados_coletados)
        time.sleep(INTERVALO)