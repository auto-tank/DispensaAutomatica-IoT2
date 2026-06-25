#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// Wi-Fi
const char* ssid = "";
const char* senha = "";

// MQTT
const char* mqtt_broker = "test.mosquitto.org";
const int mqtt_porta = 1883;
const char* mqtt_topico = "alimentador/detector_cachorro/comporta";
const char* mqtt_client_id = "alimentador_esp32_comporta";

// Servo
Servo meuServo;
const int pinoServo = 13;

// Ajuste conforme sua comporta
const int POSICAO_FECHADA = 1;
const int POSICAO_ABERTA = 50;
const int TEMPO_ABERTA_MS = 1500;

WiFiClient espClient;
PubSubClient client(espClient);

void abrirComporta() {
  Serial.println("Abrindo comporta...");
  meuServo.write(POSICAO_ABERTA);

  delay(TEMPO_ABERTA_MS);

  Serial.println("Fechando comporta...");
  meuServo.write(POSICAO_FECHADA);
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no topico: ");
  Serial.println(topic);

  String mensagem = "";

  for (unsigned int i = 0; i < length; i++) {
    mensagem += (char)payload[i];
  }

  Serial.print("Payload: ");
  Serial.println(mensagem);

  StaticJsonDocument<256> doc;
  DeserializationError erro = deserializeJson(doc, mensagem);

  if (erro) {
    Serial.print("Erro ao ler JSON: ");
    Serial.println(erro.c_str());
    return;
  }

  bool detectado = doc["detectado"] | false;
  const char* classe = doc["classe"] | "";

  if (detectado == true && String(classe) == "dog") {
    Serial.println("Cachorro detectado via MQTT. Acionando servo.");
    abrirComporta();
  } else {
    Serial.println("Mensagem recebida, mas não é comando para abrir.");
  }
}

void conectarWiFi() {
  Serial.print("Conectando ao Wi-Fi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, senha);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi conectado!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void reconectarMQTT() {
  while (!client.connected()) {
    Serial.print("Conectando ao MQTT... ");

    if (client.connect(mqtt_client_id)) {
      Serial.println("conectado!");

      client.subscribe(mqtt_topico);

      Serial.print("Inscrito no topico: ");
      Serial.println(mqtt_topico);
    } else {
      Serial.print("falhou, rc=");
      Serial.print(client.state());
      Serial.println(". Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  meuServo.setPeriodHertz(50);
  meuServo.attach(pinoServo, 500, 2400);

  Serial.println("Resetando servo para posicao fechada...");
  meuServo.write(POSICAO_FECHADA);
  delay(1000);

  conectarWiFi();

  client.setServer(mqtt_broker, mqtt_porta);
  client.setCallback(callback);

  Serial.println("Sistema pronto. Aguardando mensagem MQTT...");
}

void loop() {
  if (!client.connected()) {
    reconectarMQTT();
  }

  client.loop();
}