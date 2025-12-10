import socket
import threading
import os
import json
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.protocol import send_json, recv_json, recv_file, send_file

HOST = '0.0.0.0'
PORT = 12131
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'server_data')
GAMES_DIR = os.path.join(DATA_DIR, 'games')
DB_FILE = os.path.join(DATA_DIR, 'db.json')

database = {
    "developers": {"admin": "admin"}, 
    "players": {"p1": "p1", "p2": "p2", "p3": "p3", "p4": "p4"},
    "games": [], 
    "reviews": [],
    "play_history": []
}

available_plugins = [
    {
        "id": "room_chat",
        "name": "Room Chat Plugin",
        "description": "Enable text chat in game rooms.",
        "version": "1.0"
    }
]

active_rooms = {} 
active_game_sessions = {} 
online_users = {}

server_lock = threading.Lock()

def save_database():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DB_FILE, 'w') as file_handle:
            json.dump(database, file_handle, indent=4)
        print("[DB] Saved.")
    except Exception as error:
        print(f"[DB] Save Error: {error}")

def load_database():
    global database
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as file_handle: 
                loaded_data = json.load(file_handle)
                for key in database.keys():
                    if key in loaded_data:
                        database[key] = loaded_data[key]
            print("[DB] Loaded.")
        except Exception as error:
            print(f"[DB] Load Error: {error}")

def handle_disconnect(client_socket, username, role):
    if not username:
        return
    
    with server_lock:
        print(f"[DISCONNECT] Cleaning up for {username} ({role})")
        
        if role:
            login_key = f"{role}_{username}"
            if login_key in online_users:
                if online_users[login_key] == client_socket:
                    del online_users[login_key]
        
        for room_id, players in list(active_game_sessions.items()):
            is_in_session = False
            remaining_players = []
            
            for player in players:
                if player['socket'] == client_socket:
                    is_in_session = True
                elif player['username'] == username:
                    is_in_session = True
                else:
                    remaining_players.append(player)
            
            if is_in_session:
                active_game_sessions[room_id] = remaining_players
                
                for player in remaining_players:
                    try:
                        send_json(player['socket'], {'type': 'opponent_left'})
                    except:
                        pass
                
                if not remaining_players:
                    del active_game_sessions[room_id]

        for room_id, room_info in list(active_rooms.items()):
            if username in room_info['players']:
                room_info['players'].remove(username)
                
                if not room_info['players']:
                    del active_rooms[room_id]
                elif room_info['host'] == username:
                    room_info['host'] = room_info['players'][0]

def handle_client(client_socket, client_address):
    print(f"[CONN] New connection from {client_address}")
    current_user = None 
    current_role = None 
    
    try:
        while True:
            request = recv_json(client_socket)
            if not request:
                break
            
            command = request.get('command')

            if command == 'login':
                username = request['username']
                password = request['password']
                role = request['role']
                
                with server_lock:
                    login_key = f"{role}_{username}"
                    if login_key in online_users:
                         send_json(client_socket, {'status': 'fail', 'msg': 'Account already logged in.'})
                         continue

                    if role == 'dev':
                        table_name = 'developers'
                    else:
                        table_name = 'players'
                    
                    if role == 'dev':
                        if username not in database['developers']: 
                            database['developers'][username] = password
                            save_database()
                    
                    if username in database[table_name]:
                        if database[table_name][username] == password:
                            current_user = username
                            current_role = role
                            online_users[login_key] = client_socket
                            send_json(client_socket, {'status': 'success', 'msg': 'Login successful'})
                        else:
                            send_json(client_socket, {'status': 'fail', 'msg': 'Invalid credentials'})
                    else:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Invalid credentials'})

            elif command == 'register':
                username = request['username']
                password = request['password']
                role = request['role']
                
                with server_lock:
                    if role == 'dev':
                        table_name = 'developers'
                    else:
                        table_name = 'players'

                    if username in database[table_name]:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Username already exists'})
                    else:
                        database[table_name][username] = password
                        save_database()
                        send_json(client_socket, {'status': 'success', 'msg': 'Registration successful'})

            elif command == 'game_join':
                username = request['username']
                room_id = int(request['room_id'])
                
                with server_lock:
                    if room_id not in active_game_sessions:
                        active_game_sessions[room_id] = []
                    
                    filtered_players = []
                    current_players = active_game_sessions[room_id]
                    for player in current_players:
                        if player['username'] != username:
                            filtered_players.append(player)
                    
                    active_game_sessions[room_id] = filtered_players
                    
                    active_game_sessions[room_id].append({
                        'socket': client_socket,
                        'username': username
                    })
                    
                    player_count = len(active_game_sessions[room_id])
                    
                    if player_count == 2:
                        player1 = active_game_sessions[room_id][0]
                        player2 = active_game_sessions[room_id][1]
                        try:
                            send_json(player1['socket'], {'type': 'game_start', 'symbol': 'X', 'opponent': player2['username'], 'turn': True})
                            send_json(player2['socket'], {'type': 'game_start', 'symbol': 'O', 'opponent': player1['username'], 'turn': False})
                        except:
                            pass
                    
                    elif player_count > 2:
                        try:
                            send_json(client_socket, {'type': 'game_start', 'symbol': f'P{player_count}', 'opponent': 'Others', 'turn': False})
                        except:
                            pass

            elif command == 'game_move':
                room_id = int(request['room_id'])
                move_data = request['index']
                move_symbol = request['symbol']
                
                with server_lock:
                    if room_id in active_game_sessions:
                        for player in active_game_sessions[room_id]:
                            if player['socket'] != client_socket:
                                try:
                                    send_json(player['socket'], {
                                        'type': 'opponent_move', 
                                        'index': move_data, 
                                        'symbol': move_symbol
                                    })
                                except:
                                    pass
                        
                        if move_symbol == 'WIN':
                            print(f"[Game] Room {room_id} finished. Removing session.")
                            del active_game_sessions[room_id]
                            if room_id in active_rooms:
                                del active_rooms[room_id]


            elif command == 'game_over':
                room_id = int(request['room_id'])
                with server_lock:
                    if room_id in active_rooms:
                        active_rooms[room_id]['status'] = 'waiting'
            
            elif command == 'game_restart':
                room_id = int(request['room_id'])
                with server_lock:
                    if room_id in active_game_sessions:
                        if len(active_game_sessions[room_id]) == 2:
                            active_game_sessions[room_id].reverse()
                            player1 = active_game_sessions[room_id][0]
                            player2 = active_game_sessions[room_id][1]
                            try:
                                send_json(player1['socket'], {'type': 'game_start', 'symbol': 'X', 'opponent': player2['username'], 'turn': True})
                                send_json(player2['socket'], {'type': 'game_start', 'symbol': 'O', 'opponent': player1['username'], 'turn': False})
                                
                                if room_id in active_rooms:
                                    active_rooms[room_id]['status'] = 'playing'
                            except:
                                pass
                        else:
                            send_json(client_socket, {'type': 'opponent_left'})

            elif command == 'upload_game':
                metadata = request['meta']
                game_id = -1
                
                with server_lock:
                    existing_game = None
                    for game in database['games']:
                        if game['name'] == metadata['name']:
                            existing_game = game
                            break
                    
                    if existing_game:
                        if existing_game['author'] != current_user:
                            send_json(client_socket, {'status': 'fail', 'msg': 'Permission denied'})
                            continue
                        existing_game['version'] += 1
                        existing_game['description'] = metadata['description']
                        existing_game['type'] = metadata['type']
                        game_id = existing_game['id']
                    else:
                        game_id = len(database['games']) + 1
                        while True:
                            id_exists = False
                            for game in database['games']:
                                if game['id'] == game_id:
                                    id_exists = True
                                    break
                            if id_exists:
                                game_id += 1
                            else:
                                break
                        
                        new_game = {
                            "id": game_id,
                            "name": metadata['name'],
                            "version": 1,
                            "author": current_user,
                            "description": metadata['description'],
                            "type": metadata['type']
                        }
                        database['games'].append(new_game)
                    
                    save_database()
                
                send_json(client_socket, {'status': 'ready'})
                
                game_path = os.path.join(GAMES_DIR, str(game_id))
                os.makedirs(game_path, exist_ok=True)
                
                if recv_file(client_socket, os.path.join(game_path, 'game.py')):
                    send_json(client_socket, {'status': 'success', 'msg': 'Upload complete'})

            elif command == 'my_games':
                user_games = []
                for game in database['games']:
                    if game['author'] == current_user:
                        user_games.append(game)
                send_json(client_socket, {'status': 'success', 'data': user_games})

            elif command == 'remove_game':
                game_id = request['game_id']
                
                with server_lock:
                    has_permission = False
                    for game in database['games']:
                        if game['id'] == game_id:
                            if game['author'] == current_user:
                                has_permission = True
                            break
                    
                    if has_permission:
                        games_to_keep = []
                        for game in database['games']:
                            if game['id'] != game_id:
                                games_to_keep.append(game)
                        
                        database['games'] = games_to_keep
                        save_database()
                        
                        shutil.rmtree(os.path.join(GAMES_DIR, str(game_id)), ignore_errors=True)
                        send_json(client_socket, {'status': 'success', 'msg': 'Deleted'})
                    else:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Error'})
            
            elif command == 'get_game_details':
                game_id = request['game_id']
                
                target_game = None
                for game in database['games']:
                    if game['id'] == game_id:
                        target_game = game
                        break 

                game_reviews = []
                for review in database['reviews']:
                    if review['game_id'] == game_id:
                        game_reviews.append(review)
                
                if target_game:
                    send_json(client_socket, {'status': 'success', 'game': target_game, 'reviews': game_reviews})
                else:
                    send_json(client_socket, {'status': 'fail'})

            elif command == 'list_games':
                game_list = []
                with server_lock:
                    for game in database['games']:
                        game_info = game.copy()
                        
                        ratings = []
                        for review in database['reviews']:
                            if review['game_id'] == game['id']:
                                ratings.append(review['rating'])
                        
                        if ratings:
                            game_info['rating'] = round(sum(ratings) / len(ratings), 1)
                        else:
                            game_info['rating'] = 0.0
                        
                        game_list.append(game_info)
                
                send_json(client_socket, {'status': 'success', 'data': game_list})

            elif command == 'download_game':
                game_id = request['game_id']
                
                target_game = None
                for game in database['games']:
                    if game['id'] == game_id:
                        target_game = game
                        break
                
                file_path = os.path.join(GAMES_DIR, str(game_id), 'game.py')
                
                if target_game and os.path.exists(file_path):
                    send_json(client_socket, {'status': 'success', 'version': target_game['version']})
                    send_file(client_socket, file_path)
                else:
                    send_json(client_socket, {'status': 'fail', 'msg': 'File not found'})

            elif command == 'create_room':
                game_id = request['game_id']
                
                with server_lock:
                    game_found = False
                    game_name = "Unknown"
                    for game in database['games']:
                        if game['id'] == game_id:
                            game_found = True
                            game_name = game['name']
                            break  
                    
                    if not game_found:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Game not found'})
                        continue
                    
                    room_id = len(active_rooms) + 1
                    while True:
                        if room_id in active_rooms:
                            room_id += 1
                        else:
                            break
                    
                    active_rooms[room_id] = {
                        "id": room_id,
                        "game_id": game_id,
                        "game_name": game_name,
                        "host": current_user,
                        "players": [current_user],
                        "status": "waiting",
                        "chat_history": []  # Plugin
                    }
                    send_json(client_socket, {'status': 'success', 'room_id': room_id})

            elif command == 'list_rooms':
                send_json(client_socket, {'status': 'success', 'data': list(active_rooms.values())})

            elif command == 'join_room':
                room_id = int(request['room_id'])
                
                with server_lock:
                    if room_id in active_rooms and active_rooms[room_id]['status'] == 'waiting':
                        if current_user not in active_rooms[room_id]['players']:
                            active_rooms[room_id]['players'].append(current_user)
                        send_json(client_socket, {'status': 'success', 'game_id': active_rooms[room_id]['game_id']})
                    else:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Full'})

            elif command == 'leave_room':
                room_id = int(request['room_id'])
                with server_lock:
                    if room_id in active_rooms:
                        room = active_rooms[room_id]
                
                        if current_user in room['players']:
                            room['players'].remove(current_user)
                        
                        if current_user == room['host']:
                            # if host leave delete room
                            del active_rooms[room_id]
                            send_json(client_socket, {'status': 'success'})
                        
                        elif len(room['players']) == 0:
                            # no player 
                            del active_rooms[room_id]
                            send_json(client_socket, {'status': 'success'})
                        
                        else:
                            send_json(client_socket, {'status': 'success'})
                    else:
                        send_json(client_socket, {'status': 'fail', 'msg': 'Room not found'})
            
            elif command == 'get_room_info':
                room_id = int(request['room_id'])
                if room_id in active_rooms:
                    send_json(client_socket, {'status': 'success', 'data': active_rooms[room_id]})
                else:
                    send_json(client_socket, {'status': 'fail'})

            elif command == 'start_game':
                room_id = int(request['room_id'])
                
                with server_lock:
                    if room_id in active_rooms and active_rooms[room_id]['host'] == current_user:
                        active_rooms[room_id]['status'] = 'playing'
                        
                        game_id = active_rooms[room_id]['game_id']
                        for player_name in active_rooms[room_id]['players']:
                            already_recorded = False
                            for history in database['play_history']:
                                if history['user'] == player_name and history['game_id'] == game_id:
                                    already_recorded = True
                                    break
                            
                            if not already_recorded:
                                database['play_history'].append({"user": player_name, "game_id": game_id})
                        
                        save_database()
                        send_json(client_socket, {'status': 'success'})
                    else:
                        send_json(client_socket, {'status': 'fail'})
            
            elif command == 'submit_review':
                game_id = request['game_id']
                rating = request['rating']
                comment = request['comment']
                
                with server_lock:
                    has_played = False
                    for history in database['play_history']:
                        if history['user'] == current_user and history['game_id'] == game_id:
                            has_played = True
                            break
                    
                    if not has_played:
                        send_json(client_socket, {'status': 'fail', 'msg': 'You must play the game before reviewing it!'})
                        continue

                    already_reviewed = False
                    for review in database['reviews']:
                        if review['user'] == current_user and review['game_id'] == game_id:
                            already_reviewed = True
                            break
                    
                    if already_reviewed:
                        send_json(client_socket, {'status': 'fail', 'msg': 'You have already reviewed this game.'})
                        continue

                    database['reviews'].append({
                        "game_id": game_id,
                        "user": current_user,
                        "rating": rating,
                        "comment": comment
                    })
                    save_database()
                    send_json(client_socket, {'status': 'success'})

            elif command == 'list_plugins':
                send_json(client_socket, {'status': 'success', 'data': available_plugins})

            # PL3 : chat handle
            elif command == 'send_chat':
                room_id = int(request['room_id'])
                msg = request['msg']
                
                with server_lock:
                    if room_id in active_rooms:
                        
                        chat_entry = f"{current_user}: {msg}"
                        active_rooms[room_id]['chat_history'].append(chat_entry)
                        # max len = 50
                        if len(active_rooms[room_id]['chat_history']) > 50:
                            active_rooms[room_id]['chat_history'].pop(0)
                        send_json(client_socket, {'status': 'success'})
                    else:
                        send_json(client_socket, {'status': 'fail'})

    except Exception as error:
        print(f"[ERR] {client_address}: {error}")
    finally:
        handle_disconnect(client_socket, current_user, current_role)
        client_socket.close()

if __name__ == '__main__':
    os.makedirs(GAMES_DIR, exist_ok=True)
    load_database()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    
    print(f"Server running on {HOST}:{PORT}")
    
    while True:
        client_sock, client_addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
        thread.start()