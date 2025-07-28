import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import json
import time

probabilidade = ctrl.Antecedent(np.arange(0, 11, 1), 'probabilidade')
impacto = ctrl.Antecedent(np.arange(0, 11, 1), 'impacto')
detectabilidade = ctrl.Antecedent(np.arange(0, 11, 1), 'detectabilidade')
risco = ctrl.Consequent(np.arange(0, 11, 1), 'risco')

probabilidade['baixa'] = fuzz.trimf(probabilidade.universe, [0, 0, 5])
probabilidade['media'] = fuzz.trimf(probabilidade.universe, [0, 5, 10])
probabilidade['alta'] = fuzz.trimf(probabilidade.universe, [5, 10, 10])

impacto['baixo'] = fuzz.trimf(impacto.universe, [0, 0, 5])
impacto['medio'] = fuzz.trimf(impacto.universe, [0, 5, 10])
impacto['alto'] = fuzz.trimf(impacto.universe, [5, 10, 10])

detectabilidade['baixa'] = fuzz.trimf(detectabilidade.universe, [0, 0, 5])
detectabilidade['media'] = fuzz.trimf(detectabilidade.universe, [0, 5, 10])
detectabilidade['alta'] = fuzz.trimf(detectabilidade.universe, [5, 10, 10])

risco['baixo'] = fuzz.trimf(risco.universe, [0, 0, 4])
risco['moderado'] = fuzz.trimf(risco.universe, [2, 5, 8])
risco['alto'] = fuzz.trimf(risco.universe, [6, 8, 10])
risco['critico'] = fuzz.trimf(risco.universe, [8, 10, 10])

regra1 = ctrl.Rule(probabilidade['alta'] & impacto['alto'], risco['critico'])
regra2 = ctrl.Rule(probabilidade['media'] & impacto['alto'], risco['alto'])
regra3 = ctrl.Rule(probabilidade['alta'] & impacto['medio'], risco['alto'])
regra4 = ctrl.Rule(impacto['alto'] & detectabilidade['baixa'], risco['critico'])
regra5 = ctrl.Rule(probabilidade['baixa'] & impacto['baixo'], risco['baixo'])
regra6 = ctrl.Rule(detectabilidade['alta'], risco['baixo'])
regra7 = ctrl.Rule(probabilidade['media'] & impacto['medio'] & detectabilidade['media'], risco['moderado'])

sistema_risco_ctrl = ctrl.ControlSystem([regra1, regra2, regra3, regra4, regra5, regra6, regra7])
simulador_risco = ctrl.ControlSystemSimulation(sistema_risco_ctrl)

def sensors_to_fuzzy(sensor_data):
    TEMP_MIN_IDEAL = 2.0
    TEMP_MAX_IDEAL = 8.0
    HUMID_MAX_IDEAL = 60.0

    temp = sensor_data['temperature']
    if temp < TEMP_MIN_IDEAL:
        desvio_temp = TEMP_MIN_IDEAL - temp
    elif temp > TEMP_MAX_IDEAL:
        desvio_temp = temp - TEMP_MAX_IDEAL
    else:
        desvio_temp = 0
    
    # Mapeia um desvio de 0-10°C para uma escala de impacto de 0-10.
    impacto_calculado = np.clip(desvio_temp * 2, 0, 10)

    # Cálculo da PROBABILIDADE DE FALHA (Qual a chance de algo dar errado?)
    humid = sensor_data['humidity']
    prob_base = 0
    # Umidade acima do ideal aumenta a probabilidade de problemas (mofo, entre outros.)
    if humid > HUMID_MAX_IDEAL:
        prob_base += (humid - HUMID_MAX_IDEAL) / 5 # A cada 5% acima, aumenta 1 ponto

    # Temperatura
    prob_base += desvio_temp * 0.5
    probabilidade_calculada = np.clip(prob_base, 0, 10)

    # Cálculo da DETECTABILIDADE (O quão confiável e visível é o nosso sistema?)
    # Detectabilidade é alta (bom) se temos dados de GPS e o horário é recente.
    # Se não temos GPS ou o dado é antigo, a detectabilidade é baixa (ruim).
    detect_base = 10 
    lat = sensor_data['gpsLatitude']
    lon = sensor_data['gpsLongitude']
    timestamp = sensor_data['timestamp']

    # Condições
    
    if lat == 0.0 and lon == 0.0:
        detect_base -= 7
    
    tempo_atual_simulado = int(time.time())
    if (tempo_atual_simulado - timestamp) > 300:
        detect_base -= 8
    detectabilidade_calculada = np.clip(detect_base, 0, 10)

    print("\n| >>> Camada de Tradução (Sensores -> Fuzzy)")
    print(f"| Impacto (0-10): {impacto_calculado:.2f}")
    print(f"| Probabilidade (0-10): {probabilidade_calculada:.2f}")
    print(f"| Detectabilidade (0-10): {detectabilidade_calculada:.2f}")

    return {
        "probabilidade": probabilidade_calculada,
        "impacto": impacto_calculado,
        "detectabilidade": detectabilidade_calculada
    }

def processar_payload_mqtt(json_payload, sim):
    # Recebe o payload do sensor e executa a inferência fuzzy.
    print("-----------------------------------\n")
    print("| >>> Nova leitura recebida via MQTT" + " (Simulação)" if sim else " (Real)")
    sensor_data = json.loads(json_payload)
    print(f"| Payload Bruto: {sensor_data}")

    variaveis_fuzzy = sensors_to_fuzzy(sensor_data)

    simulador_risco.input['probabilidade'] = variaveis_fuzzy['probabilidade']
    simulador_risco.input['impacto'] = variaveis_fuzzy['impacto']
    simulador_risco.input['detectabilidade'] = variaveis_fuzzy['detectabilidade']

    start_time = time.perf_counter()
    simulador_risco.compute()
    end_time = time.perf_counter()
    
    tempo_inferencia_ms = (end_time - start_time) * 1000
    risco_calculado = simulador_risco.output['risco']

    print("\n| >>> Resultado da Inferência Fuzzy")
    print(f"| Nível de Risco Calculado (0-10): {risco_calculado:.2f}")
    print(f"| Telemetria - Tempo de Inferência: {tempo_inferencia_ms:.4f} ms")
    print("-----------------------------------\n")