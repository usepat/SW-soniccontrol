import socket

def send_command(command, host='127.0.0.1', port=1024):
    # Create a TCP/IP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server listening on host:port
        s.connect((host, port))
        
        # Send a command (string). Encode to bytes.
        s.sendall(command.encode('utf-8'))
        
        # Optionally, read response if the server sends any
        response = s.recv(1024).decode('utf-8')
        return response
    except socket.error as e:
        print(f"Socket error occurred: {e}")
        return None
    finally:
        s.close()

if __name__ == "__main__":
    # Example usage: send a command to the server
    response = send_command("tsFlag=E31", host="127.0.0.1", port=1024)
    if response is not None:
        print("Server response:", response)
    else:
        print("No response or error occurred")
