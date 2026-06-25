from ultralytics import YOLO
import cv2
import json
import os
import time  # Importação adicionada para o controle do cooldown
import tkinter as tk
from datetime import datetime
import paho.mqtt.client as mqtt

TAMANHO_MAXIMO_EXIBICAO = 700
NOME_JANELA = "Resultado da deteccao"
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORTA = 1883
MQTT_TOPICO = "alimentador/detector_cachorro/comporta"
MQTT_CLIENT_ID = "alimentador_detector_cachorro_python"
LOCAL_DISPOSITIVO = "notebook_alimentador"


def redimensionar_para_exibicao(imagem, tamanho_maximo=TAMANHO_MAXIMO_EXIBICAO):
    altura, largura = imagem.shape[:2]
    escala = min(tamanho_maximo / largura, tamanho_maximo / altura, 1)

    if escala == 1:
        return imagem

    nova_largura = int(largura * escala)
    nova_altura = int(altura * escala)
    return cv2.resize(imagem, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)


def centralizar_janela(nome_janela, imagem):
    altura_imagem, largura_imagem = imagem.shape[:2]

    tela = tk.Tk()
    tela.withdraw()
    largura_tela = tela.winfo_screenwidth()
    altura_tela = tela.winfo_screenheight()
    tela.destroy()

    posicao_x = max((largura_tela - largura_imagem) // 2, 0)
    posicao_y = max((altura_tela - altura_imagem) // 2, 0)
    cv2.moveWindow(nome_janela, posicao_x, posicao_y)


def enviar_mqtt(confianca):
    payload = {
        "evento": "cachorro_detectado",
        "detectado": True,
        "classe": "dog",
        "confianca": round(confianca, 2),
        "local": LOCAL_DISPOSITIVO,
        "data_hora": datetime.now().isoformat()
    }

    try:
        cliente = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID
        )
        cliente.connect(MQTT_BROKER, MQTT_PORTA, 60)
        resultado = cliente.publish(MQTT_TOPICO, json.dumps(payload))
        resultado.wait_for_publish()
        cliente.disconnect()

        if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"MQTT: mensagem enviada para o topico '{MQTT_TOPICO}'.")
        else:
            print(f"MQTT: falha ao enviar mensagem. Codigo: {resultado.rc}")
    except Exception as erro:
        print(f"MQTT: erro ao enviar mensagem: {erro}")


def iniciar_deteccao_webcam(model):
    # Alterar isso de acordo com quantas webcams conectadas
    cap = cv2.VideoCapture(1)
    
    if not cap.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    # Configuração do Cooldown
    cooldown_segundos = 60
    ultimo_envio = 0  

    print("Iniciando feed da webcam. Pressione 'q' na janela do vídeo para sair.")

    while True:
        sucesso, frame = cap.read()
        if not sucesso:
            print("Falha ao capturar imagem da webcam.")
            break

        # Passa o frame para o YOLO
        resultados = model(frame, verbose=False)

        cachorro_detectado = False
        maior_confianca = 0.0

        for resultado in resultados:
            for box in resultado.boxes:
                cls_id = int(box.cls[0])
                nome_classe = model.names[cls_id]
                confianca = float(box.conf[0])

                # Certeza maior que 75% (0.75)
                if nome_classe == "dog" and confianca > 0.75:
                    cachorro_detectado = True
                    maior_confianca = max(maior_confianca, confianca)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Desenha a caixa ao redor do cachorro
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"Cachorro {confianca:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

        # Lógica de controle de tempo (Cooldown)
        tempo_atual = time.time()
        em_cooldown = (tempo_atual - ultimo_envio) < cooldown_segundos

        if cachorro_detectado:
            if not em_cooldown:
                print(f"Cachorro detectado com {maior_confianca*100:.1f}% de certeza! Acionando comportas...")
                enviar_mqtt(maior_confianca)
                ultimo_envio = tempo_atual
        
        # Interface Visual
        if em_cooldown:
            tempo_restante = cooldown_segundos - (tempo_atual - ultimo_envio)
            cv2.putText(frame, f"Aguarde: {tempo_restante:.0f}s", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Pronto para liberar racao", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Mostra o feed de vídeo em tempo real
        frame_exibicao = redimensionar_para_exibicao(frame)
        cv2.imshow(NOME_JANELA, frame_exibicao)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Encerrando o sistema...")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Carrega o modelo
    try:
        model = YOLO("yolo11n.pt")
        print("Modelo YOLO carregado com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        exit()

    # Inicia o loop da webcam
    iniciar_deteccao_webcam(model)