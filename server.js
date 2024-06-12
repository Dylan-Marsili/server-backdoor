const net = require('net');
const clients = [];
const os = require('os');
const dns = require('dns');

function obtenerIPDelHost() {
    const interfaces = os.networkInterfaces();
    for (let iface in interfaces) {
        for (let alias of interfaces[iface]) {
            if (alias.family === 'IPv4' && !alias.internal) {
                return alias.address;
            }
        }
    }
    return null;
}
const PORT = 5001;
const ADMIN_KEY = 'admin123';  // Clave para identificar al admin

const server = net.createServer((socket) => {
    let isAdmin = false;
    let clientKey = `${socket.remoteAddress}:${socket.remotePort}`;

    if (socket.remoteAddress === '::1') {
        socket.end();
        return;
    }

    socket.once('data', (data) => {
        const message = data.toString().trim();

        if (message === ADMIN_KEY) {
            isAdmin = true;
            console.log('Admin conectado');
            socket.write('Conexión como admin exitosa. Use los comandos "list", "connect [client_id]", "disconnect [client_id]", "exit".\n');
            handleAdmin(socket);
        } else {
            clients.push({ key: clientKey, socket });
            console.log(`Cliente conectado: ${clientKey}`);
            handleClient(socket, clientKey);
        }
    });

    socket.on('end', () => {
        const index = clients.findIndex(client => client.key === clientKey);
        if (index !== -1) {
            clients.splice(index, 1);
            console.log(`Cliente desconectado: ${clientKey}`);
        } else if (isAdmin) {
            console.log('Admin desconectado');
        }
    });
    socket.on('error', (err) => {
        const index = clients.findIndex(client => client.key === clientKey);
        if (index !== -1) {
            clients.splice(index, 1);
            console.error(`Error en el cliente ${clientKey}: ${err.message}`);
        } else if (isAdmin) {
            console.error(`Error en el admin: ${err.message}`);
        }
    });
});

function handleClient(socket, clientKey) {
    socket.on('data', (data) => {
        const message = data.toString().trim();
        if (message === 'exit_client') {
            socket.end();
        } else {
            socket.write(`${message}\n`);
        }
    });
}

function handleAdmin(socket) {
    socket.on('data', (data) => {
        const command = data.toString().trim();
        console.log(`Comando del admin: ${command}`);
        if (command === 'exit') {
            socket.end();
        } else if (command === 'list') {
            socket.write(`Clientes conectados:\n${clients.map(client => client.key).join('\n')}\n`);
        } else if (command.startsWith('connect')) {
            const [, clientKey] = command.split(' ');
            const client = clients.find(client => client.key === clientKey);
            if (client) {
                const clientSocket = client.socket;
                handleAdminToClient(socket, clientSocket);
            } else {
                socket.write(`Cliente ${clientKey} no encontrado.\n`);
            }
        } else if (command.startsWith('disconnect')) {
            const [, clientKey] = command.split(' ');
            const index = clients.findIndex(client => client.key === clientKey);
            if (index !== -1) {
                const clientSocket = clients[index].socket;
                clientSocket.end();
                clients.splice(index, 1);
                socket.write(`Cliente ${clientKey} desconectado.\n`);
            } else {
                socket.write(`Cliente ${clientKey} no encontrado.\n`);
            }
        }
    });
}

function handleAdminToClient(adminSocket, clientSocket) {
    const adminDataHandler = (data) => {
        const message = data.toString().trim();
        if (message === 'exit_client') {
            adminSocket.removeListener('data', adminDataHandler);
            adminSocket.write('Desconectado del cliente\n');
        } else {
            clientSocket.write(message)
            clientSocket.once('data', (clientData) => {
                adminSocket.write(clientData.toString());
            });
            
        }
    };
    adminSocket.on('data', adminDataHandler);
}

server.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${obtenerIPDelHost()}:${PORT}`);
});
