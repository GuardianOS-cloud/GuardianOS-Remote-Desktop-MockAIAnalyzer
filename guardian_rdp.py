
import socket
import threading
import cv2
import numpy as np
import pyautogui
import zlib
import time
import json
from PIL import Image

# Модуль имитации ИИ-анализа (без реального API)
class MockAIAnalyzer:
    def analyze_screen(self, frame):
        """Имитация обнаружения объектов на экране"""
        height, width = frame.shape[:2]
        x, y = np.random.randint(0, width-100), np.random.randint(0, height-100)
        cv2.rectangle(frame, (x, y), (x+100, y+100), (0, 255, 0), 2)
        cv2.putText(frame, "GUARDIAN AI: Обнаружена подозрительная активность", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame

# Функции сжатия
def compress(data):
    return zlib.compress(data)

def decompress(data):
    return zlib.decompress(data)

# Серверная часть
class RemoteDesktopServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.ai_analyzer = MockAIAnalyzer()
        print(f"[*] Guardian OS Server слушает на {host}:{port}")

    def handle_client(self, client_socket):
        try:
            while True:
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                analyzed_frame = self.ai_analyzer.analyze_screen(frame)
                _, buffer = cv2.imencode('.jpg', analyzed_frame)
                compressed = compress(buffer.tobytes())
                data = json.dumps({'size': len(compressed)}).encode()
                client_socket.send(len(data).to_bytes(4, 'big'))
                client_socket.send(data)
                client_socket.sendall(compressed)
                time.sleep(0.1)
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            client_socket.close()

    def start(self):
        while True:
            client_sock, addr = self.server.accept()
            print(f"[+] Подключение от {addr[0]}:{addr[1]}")
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_sock,))
            client_thread.daemon = True
            client_thread.start()

# Клиентская часть
class RemoteDesktopClient:
    def __init__(self, server_ip, port=5000):
        self.server_ip = server_ip
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

    def connect_to_server(self):
        self.client_socket.connect((self.server_ip, self.port))
        print("[*] Подключено к серверу Guardian OS")

    def receive_stream(self):
        try:
            while True:
                size_data = self.client_socket.recv(4)
                if not size_data: 
                    break
                json_size = int.from_bytes(size_data, 'big')
                json_data = self.client_socket.recv(json_size)
                if not json_data:
                    break

                meta = json.loads(json_data.decode())
                compressed_size = meta['size']

                compressed_data = b''
                while len(compressed_data) < compressed_size:
                    remaining = compressed_size - len(compressed_data)
                    compressed_data += self.client_socket.recv(4096 if remaining > 4096 else remaining)

                data = decompress(compressed_data)
                img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), 1)
                cv2.imshow('Guardian OS - Удалённый рабочий стол', img)

                if cv2.waitKey(1) == ord('q'):
                    break

        except Exception as e:
            print(f"Ошибка соединения: {e}")
        finally:
            cv2.destroyAllWindows()
            self.client_socket.close()

# Пример использования
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование:")
        print("  Сервер: python script.py --server")
        print("  Клиент: python script.py --client <ip_адрес_сервера>")
        sys.exit(1)

    if sys.argv[1] == "--server":
        server = RemoteDesktopServer()
        server.start()
    elif sys.argv[1] == "--client" and len(sys.argv) >= 3:
        client = RemoteDesktopClient(sys.argv[2])
        client.receive_stream()
