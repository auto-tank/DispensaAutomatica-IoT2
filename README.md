# Alimentador Automático IoT com Visão Computacional

Este projeto integra Inteligência Artificial (Visão Computacional) e Internet das Coisas (IoT) para automatizar a liberação de ração para cães. 

O sistema utiliza um script Python rodando localmente que captura imagens de uma webcam e as processa através da rede neural YOLO. Quando um cachorro é detectado com alto grau de confiança (acima de 75%), o script atua como um publicador MQTT, enviando um sinal via internet. Na outra ponta, um microcontrolador ESP32 conectado ao Wi-Fi assina o tópico MQTT, recebe o comando (JSON) e aciona um servo motor para abrir a comporta de ração.

**Autores:** Italo Henrique Soares dos Santos, Lucas de Souza Bueno, Pedro Lucas Alves Mattos e Rodrigo Reis do Valle

## Arquitetura do Sistema

* **Câmera/Servidor (`trabIOT.py`):** Captura o feed de vídeo, realiza a inferência com YOLOv11 (ou v8) e envia comandos para o broker MQTT. Possui um *cooldown* configurável (padrão de 60s) para evitar liberação contínua de ração.
* **Microcontrolador (`ServoMechanism.ino`):** Conecta-se à rede, escuta ativamente o broker MQTT (`test.mosquitto.org`) e converte o sinal digital em movimento mecânico através do servo motor.

## Requisitos e Dependências

### Hardware
* Computador/Notebook com webcam (ex: Logitech BRIO 100).
* Placa ESP32.
* Servo Motor (ex: SG90 ou MG995, dependendo do torque necessário para a comporta).
* Mecanismo físico da comporta para ração.

### Software (Python)
Para rodar o servidor de detecção, instale as dependências:
```bash
pip install ultralytics opencv-python paho-mqtt