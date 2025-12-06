import socket
import struct
import json
import os

def send_json(socket_connection, data_dictionary):
    try:
        json_string = json.dumps(data_dictionary)
        json_bytes = json_string.encode('utf-8')
        message_length = len(json_bytes)
        
        header = struct.pack('>I', message_length)
        
        socket_connection.sendall(header + json_bytes)
        return True
    except Exception as error:
        print(f"[Protocol] Send Error: {error}")
        return False

def recv_json(socket_connection):
    try:
        header_data = receive_all_bytes(socket_connection, 4)
        
        if not header_data:
            return None
        
        message_length = struct.unpack('>I', header_data)[0]
 
        json_bytes = receive_all_bytes(socket_connection, message_length)
        
        if not json_bytes:
            return None
            
        json_string = json_bytes.decode('utf-8')
        data_dictionary = json.loads(json_string)
        
        return data_dictionary
    except Exception as error:
        return None

def send_file(socket_connection, file_path):
    if not os.path.exists(file_path):
        return False
    
    file_size = os.path.getsize(file_path)
    header = struct.pack('>Q', file_size)
    socket_connection.sendall(header)
    
    with open(file_path, 'rb') as file_handle:
        while True:
            chunk_data = file_handle.read(4096)
            if not chunk_data:
                break
            socket_connection.sendall(chunk_data)
            
    return True

def recv_file(socket_connection, save_path):
    header_data = receive_all_bytes(socket_connection, 8)
    
    if not header_data:
        return False
        
    file_size = struct.unpack('>Q', header_data)[0]
    
    directory_path = os.path.dirname(save_path)
    if directory_path:
        os.makedirs(directory_path, exist_ok=True)
    
    total_received = 0
    with open(save_path, 'wb') as file_handle:
        while total_received < file_size:
            remaining_bytes = file_size - total_received
            
            if remaining_bytes < 4096:
                chunk_size = remaining_bytes
            else:
                chunk_size = 4096
                
            chunk_data = receive_all_bytes(socket_connection, chunk_size)
            
            if not chunk_data:
                break
                
            file_handle.write(chunk_data)
            total_received += len(chunk_data)
            
    return True

def receive_all_bytes(socket_connection, target_length):
    received_data = b''
    
    while len(received_data) < target_length:
        bytes_needed = target_length - len(received_data)
        
        try:
            packet = socket_connection.recv(bytes_needed)
            if not packet:
                return None
            received_data += packet
        except:
            return None
            
    return received_data