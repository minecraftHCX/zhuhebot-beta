import socket


def start_server(host='0.0.0.0', port=8080):
    # 创建一个socket对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定主机和端口
    server_socket.bind((host, port))
    # 监听连接
    server_socket.listen(5)
    print(f"Server started at {host}:{port}, waiting for connections...")

    while True:
        # 接受客户端连接
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        # 获取客户端发送的数据
        data = client_socket.recv(1024).decode('utf-8')
        print(f"Received data: {data}")
        # 响应客户端
        client_socket.send("HTTP/1.1 200 OK\r\n\r\nHello, Client!".encode('utf-8'))
        # 关闭客户端连接
        client_socket.close()


if __name__ == "__main__":
    start_server()
