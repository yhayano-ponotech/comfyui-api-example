import json
from urllib import request, parse
import random
import os
import ssl
import certifi
import asyncio
import websockets

# ComfyUIのサーバーアドレスを設定
SERVER_ADDRESS = "YOUR_SERVER_ADDRESS"

# workflowファイルのパス
WORKFLOW_PATH = 'workflow_api.json'

# certifiから証明書を取得し、SSLコンテキストを作成（安全な通信を確保）
ssl_context = ssl.create_default_context(cafile=certifi.where())

# imagesフォルダを作成（存在しない場合）
if not os.path.exists('images'):
    os.makedirs('images')

# WebSocket接続を介してサーバーの完了メッセージを待機
async def listen_for_completion():
    uri = f"wss://{SERVER_ADDRESS}/ws"  # WebSocketサーバーのURI
    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        print("WebSocket接続が確立されました")  # 接続が成功したら表示
        try:
            while True:
                # サーバーからのメッセージを30秒間待機
                message = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(message)  # JSON形式のメッセージを辞書に変換
                print(data)  # 受信したメッセージを表示
                status = data['type']  # メッセージタイプを取得
                if status == 'status':
                    # キューに残っているタスク数を取得
                    queue_remaining = data['data']['status']['exec_info']['queue_remaining']
                    if queue_remaining == 0:
                        print("画像生成が完了しました")  # 画像生成が完了したら表示
                        break  # ループを終了
        except asyncio.TimeoutError:
            print("タイムアウト: サーバーからの応答がありません")  # タイムアウト時のエラーメッセージ

# プロンプトをキューに追加する関数
def queue_prompt(prompt):
    p = {"prompt": prompt}  # プロンプトを辞書形式で作成
    data = json.dumps(p).encode('utf-8')  # JSON形式にエンコード
    req = request.Request(f"https://{SERVER_ADDRESS}/prompt", data=data)  # POSTリクエストを作成
    response = request.urlopen(req, context=ssl_context)  # サーバーにリクエストを送信
    return response.read()  # レスポンスを返す

# 指定されたprompt_idの履歴を取得する関数
def get_history(prompt_id):
    with request.urlopen(f"https://{SERVER_ADDRESS}/history/{prompt_id}", context=ssl_context) as response:
        return json.loads(response.read())  # レスポンスを辞書形式で返す

# 指定された画像ファイルを取得する関数
def get_image(filename, subfolder, folder_type):
    data = {
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type  # ファイルタイプ（例: 'output'）
    }
    url_values = parse.urlencode(data)  # URLクエリパラメータをエンコード
    with request.urlopen(f"https://{SERVER_ADDRESS}/view?{url_values}", context=ssl_context) as response:
        return response.read()  # 画像データを返す

# メインプログラム
if __name__ == '__main__':
    # workflow_api.jsonファイルを読み込む
    with open(WORKFLOW_PATH, 'r') as file:
        prompt = json.load(file)  # JSON形式のデータを辞書として読み込む
    
    # プロンプトの内容を変更する例

    # CLIPTextEncodeノードのテキストを変更
    prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

    # KSamplerノードのシードをランダムに設定
    prompt["3"]["inputs"]["seed"] = random.randint(1, 1000000)

    # プロンプトをキューに追加し、サーバーのレスポンスを取得
    response = queue_prompt(prompt)
    print('response' + str(response))  # サーバーからのレスポンスを表示

    # 画像生成が完了するまでWebSocketで待機
    asyncio.run(listen_for_completion())

    # レスポンスをJSON形式の辞書に変換
    response_json = json.loads(response)

    # prompt_idをレスポンスから取得
    prompt_id = response_json.get('prompt_id', None)

    # 取得したprompt_idの履歴をサーバーから取得
    history = get_history(prompt_id)
    print(history)  # 取得した履歴を表示

    # 画像情報を履歴から取得
    output_images = history[prompt_id]['outputs']['9']['images']
    
    # 取得した画像の情報をループで処理
    for image in output_images:
        filename = image['filename']  # ファイル名を取得
        image_type = image['type']  # 画像のタイプを取得
        subfolder = image['subfolder']  # サブフォルダ情報を取得
        print(f"Filename: {filename}, Type: {image_type}, Subfolder: {subfolder}")  # 画像情報を出力

        # 画像データをサーバーから取得
        image_data = get_image(filename, subfolder, 'output')
        
        # 画像をimagesフォルダ内に保存するパスを作成
        save_path = os.path.join('images', filename)

        # ローカルファイルに画像を書き込み（imagesフォルダ内）
        with open(save_path, 'wb') as file:
            file.write(image_data)
