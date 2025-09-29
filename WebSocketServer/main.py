from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

import sqlite3
import os
import struct

app = FastAPI()
connection = None

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://192.168.1.158:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

#cmd.CommandText = @"CREATE TABLE data(id INTEGER PRIMARY KEY,finger VARCHAR(255), action BOOL, sensor_id INTEGER, signal BLOB, 
#                   length INTEGER, frequency INTEGER, date DATE, error BOOL)";

def createDataBase(file_path):
    if os.path.exists(file_path):
        print(f"Файл '{file_path}' существует.")
    else:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE Data (
                    Id	INTEGER NOT NULL UNIQUE,
                    SensorId	NUMERIC NOT NULL,
                    Data	BLOB NOT NULL,                                                      
                    Length  INTEGER NOT NULL,
                    Time	INTEGER NOT NULL,
                    PRIMARY KEY("Id" AUTOINCREMENT),
                    CONSTRAINT SensorId FOREIGN KEY("SensorId") REFERENCES Sensors("SensorId")
                )
            """)
            #Data BLOB  -  углы будут храниться в БД как бинарные значения

            cursor.execute("""
                CREATE TABLE "Sensors" (
                    SensorId	INTEGER NOT NULL UNIQUE,
                    Type	TEXT NOT NULL,
                    VFrom	INTEGER NOT NULL,
                    VTo	INTEGER NOT NULL,
                )
            """)

            cursor.execute("""
                CREATE TABLE "Users" (
                    UserId	INTEGER NOT NULL UNIQUE,
                    Name	TEXT NOT NULL,
                    SecondName	TEXT NOT NULL,
                    Password TEXT NOT NULL,
                    PRIMARY KEY("UserId" AUTOINCREMENT)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE "UserToSensor" (
                    UserId      INTEGER NOT NULL,
                    SensorId	INTEGER NOT NULL,
                )
            """)

            conn.commit()
            print("Базы данных и таблица успешно созданы.")
            #Заглушка
            addRecordsSensors(conn,'Stm',100, 300)
            addRecordsUsers(conn,'Admin','Admin','Admin123')
            #
        except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")
        finally:
            if conn:
                conn.close()
                print("Соединение с базой данных закрыто.")

def openDataBase(file_path):
    conn = sqlite3.connect(file_path)
    return conn

def closeDataBase(conn):
    conn.close()

def addRecordsData(connection, SensorId: int, Data: bytes, Length: int, Time: int):
    cursor = connection.cursor()
    try:
        sql_insert_Data = "INSERT INTO Data (SensorId, Data, Length, Time) VALUES (?,?,?,?)"
        cursor.execute(sql_insert_Data,(SensorId, Data, Length, Time))
        
        connection.commit()
        print("Данные о сигнале успешно добавлены!")
    except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")
    
def addRecordsSensors(connection, SensorId: int, Type: str, VFrom: int, VTo: int):
    cursor = connection.cursor()
    try:
        sql_insert_Sensors = "INSERT INTO Sensors (SensorId, Type, VFrom, VTo) VALUES (?,?,?,?)"
        cursor.execute(sql_insert_Sensors,(SensorId, Type, VFrom, VTo))
        
        connection.commit()
        print("Данные о сенсорах успешно добавлены!")
    except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")
            
def addRecordsUsers(connection, Name: str, SecondName: str, Password: str):
    cursor = connection.cursor()
    try:
        sql_insert_Users = "INSERT INTO Users (Name, SecondName, Password) VALUES (?,?,?)"
        cursor.execute(sql_insert_Users,(Name, SecondName, Password))
        
        connection.commit()
        print("Данные о пользователях успешно добавлены!")
    except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")

#Заглушка
def selectFirstUser(connection):
    cursor = connection.cursor()
    try:
        sql_select = "SELECT UserId FROM Users LIMIT 1"
        cursor.execute(sql_select)
        rows = cursor.fetchall()
        for row in rows:
            UserId = row[0]
            #print(f"ID: {UserId}")
            return UserId
    except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")
    return 1

    
def selectFirstSensor(connection):
    cursor = connection.cursor()
    try:
        sql_select = "SELECT SensorId FROM Sensors LIMIT 1"
        cursor.execute(sql_select)
        rows = cursor.fetchall()
        for row in rows:
            SensorId = row[0]
            #print(f"ID: {SensorId}")
            return SensorId
    except sqlite3.Error as e:
            print(f"Ошибка при работе с SQLite: {e}")
    return 1
#    

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive()
        #data = await websocket.receive_bytes()
        if message.get('text') is not None: 
            print(message['text'])
        elif message.get('bytes') is not None:
            print(message['bytes'])
            unpack = struct.unpack('ii8s', message["bytes"])
            print(unpack)
            addRecordsData(connection,unpack[0],unpack[2],len(unpack[2]),unpack[1])

if __name__ == "__main__":
    import uvicorn
    file_path = 'DataBaseAngles.db'
    createDataBase(file_path)
    connection = openDataBase(file_path)
    #Заглушка
    UserId = selectFirstUser(connection)
    SensorId = selectFirstSensor(connection)
    #
    #addRecordsData(connection, SensorId, bytes(10), 10, 0)
    uvicorn.run(app, host="192.168.1.158", port=8000)
    closeDataBase(connection)

    # uvicorn main:app --reload --host 192.168.1.158 --port 8000