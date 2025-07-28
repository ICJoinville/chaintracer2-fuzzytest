import time
import sys
from fuzzy import processar_payload_mqtt
from mqtt import connect

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print(">>> Uso: python main.py <sim|real>")
        sys.exit(1)

    modo = sys.argv[1].lower()
    if modo not in ['sim', 'real']:
        print(">>> Uso: python main.py <sim|real>")
        sys.exit(1)

    if modo == 'sim':
        print(">>> Modo Simulação Ativado")
        # Situação típica
        # Temperatura e umidade ideais, GPS funcionando, data e hora recente.
        payload_normal = f'{{"temperature":5.5, "pressure":1013, "humidity":50, "gpsLatitude":-26.30, "gpsLongitude":-48.84, "timestamp":{int(time.time() * 1000)}}}'
        processar_payload_mqtt(payload_normal, True)

        # Situação crítica
        # Temperatura muito alta, umidade alta, GPS falhou (0,0) e o dado é antigo.
        payload_critico = f'{{"temperature":15.0, "pressure":1013, "humidity":75, "gpsLatitude":0.0, "gpsLongitude":0.0, "timestamp":{int(time.time() * 1000) - 600000}}}'
        processar_payload_mqtt(payload_critico, True)
    elif modo == 'real':
        print(">>> Modo Real Ativado")
        connect()