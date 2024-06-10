import socket
import threading

clients = {}  # Diccionario para almacenar conexiones de clientes y direcciones
admin_connection = None  # Conexión del cliente especial (admin)
lock = threading.Lock()  # Para proteger el acceso concurrente al diccionario de clientes

def handle_client(conn, address):
    client_id = f"{address[0]}:{address[1]}"  # Identificador único para el cliente
    with lock:
        clients[client_id] = conn  # Agregar cliente al diccionario

    print(f"Conexión desde: {address}")

    try:
        while True:
            command = conn.recv(1024).decode('utf-8', errors='ignore')
            if not command:
                break

            if command == 'exit_client':
                break

            data = b''
            while True:
                part = conn.recv(4096)
                data += part
                if len(part) < 4096:
                    break

            try:
                print(f"Salida del cliente {client_id}:\n{data.decode('utf-8', errors='ignore')}")
            except UnicodeDecodeError:
                print(f"Error de decodificación en la salida del cliente {client_id}")

    except ConnectionResetError:
        print(f"Conexión resetada por el cliente {client_id}")
    except ConnectionAbortedError:
        print(f"Conexión abortada por el cliente {client_id}")
    finally:
        with lock:
            if client_id in clients:
                del clients[client_id]  # Eliminar cliente del diccionario cuando se desconecta
        conn.close()

def handle_admin(conn, address):
    global admin_connection
    admin_connection = conn
    print(f"Admin conectado desde: {address}")

    while True:
        try:
            command = conn.recv(1024).decode('utf-8', errors='ignore')
            if not command:
                break

            if command.lower() == 'exit':
                print("Cerrando conexión del admin...")
                conn.close()
                break

            if command.startswith("connect"):
                _, client_id = command.split(' ', 1)
                with lock:
                    if client_id in clients:
                        conn.send(f"Conectando al cliente {client_id}".encode('utf-8'))
                        handle_interactive_session(conn, clients[client_id])
                    else:
                        conn.send(f"Cliente {client_id} no encontrado.".encode('utf-8'))
            elif command == "list":
                with lock:
                    response = "\n".join(clients.keys())
                conn.send(response.encode('utf-8'))
            elif command.startswith("disconnect"):
                _, client_id = command.split(' ', 1)
                with lock:
                    if client_id in clients:
                        clients[client_id].send('exit_client'.encode('utf-8'))
                        clients[client_id].close()
                        del clients[client_id]
                        conn.send(f"Cliente {client_id} desconectado.".encode('utf-8'))
                    else:
                        conn.send(f"Cliente {client_id} no encontrado.".encode('utf-8'))

        except ConnectionResetError:
            print("Conexión resetada por el admin")
            break
        except ConnectionAbortedError:
            print("Conexión abortada por el admin")
            break

def handle_interactive_session(admin_conn, client_conn):
    while True:
        try:
            command = admin_conn.recv(1024).decode('utf-8', errors='ignore')
            if command == 'exit_client':
                break
            client_conn.send(command.encode('utf-8'))
            response = client_conn.recv(4096).decode('utf-8', errors='ignore')
            admin_conn.send(response.encode('utf-8'))
        except ConnectionResetError:
            break
        except ConnectionAbortedError:
            break

def server_program():
    host = '172.17.255.255'  # IP local
    client_port = 53454  # Puerto para los clientes normales
    admin_port = 53446  # Puerto específico para el cliente especial (admin)

    # Configurar socket para clientes normales
    client_socket = socket.socket()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del socket
    client_socket.bind((host, client_port))
    client_socket.listen(5)  # Permitir hasta 5 conexiones en cola

    # Configurar socket para cliente especial (admin)
    admin_socket = socket.socket()
    admin_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del socket
    admin_socket.bind((host, admin_port))
    admin_socket.listen(1)  # Solo una conexión de admin permitida

    print(f"Servidor escuchando en puertos {client_port} (clientes) y {admin_port} (admin)")

    def accept_clients():
        while True:
            conn, address = client_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, address))
            client_thread.start()

    def accept_admin():
        while True:
            conn, address = admin_socket.accept()
            handle_admin(conn, address)

    # Crear y ejecutar hilos para aceptar clientes y admin
    client_thread = threading.Thread(target=accept_clients)
    admin_thread = threading.Thread(target=accept_admin)
    client_thread.start()
    admin_thread.start()

    client_thread.join()
    admin_thread.join()

if __name__ == '__main__':
    server_program()
