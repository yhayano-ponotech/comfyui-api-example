import json
from urllib import request, parse
import random
import os
import ssl
import certifi
import asyncio
import websockets
import uuid

# ComfyUIのサーバーアドレスを設定
SERVER_ADDRESS = "tensorboard-nyi5mte01b.clg07azjl.paperspacegradient.com"
CLIENT_ID = str(uuid.uuid4())

# workflowファイルのパス
WORKFLOW_PATH = 'workflow_api.json'

# certifiから証明書を取得し、SSLコンテキストを作成（安全な通信を確保）
ssl_context = ssl.create_default_context(cafile=certifi.where())

# imagesフォルダを作成（存在しない場合）
if not os.path.exists('images'):
    os.makedirs('images')
    
# imagesフォルダ内で既存の画像ファイル名をチェックし、次の連番を決定する関数
def get_next_image_number():
    existing_files = os.listdir('images')
    max_num = -1
    for file in existing_files:
        if file.startswith("ComfyUI_") and file.endswith(".png"):
            try:
                num = int(file.replace("ComfyUI_", "").replace(".png", ""))
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return max_num + 1  # 次の連番を返す

# WebSocket接続を介してサーバーの完了メッセージを待機
async def get_images(prompt_id):
    uri = f"wss://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}"  # WebSocketサーバーのURI
    output_images = []
    current_node = ''
    
    async with websockets.connect(uri, ssl=ssl_context, max_size=10*1024*1024) as websocket:
        print("WebSocket接続が確立されました")  # 接続が成功したら表示
    
        try:
            while True:
                # サーバーからのメッセージを30秒間待機
                out = await asyncio.wait_for(websocket.recv(), timeout=30)
                if isinstance(out, str):
                    message = json.loads(out)  # JSON形式のメッセージを辞書に変換
                    print(message)  # 受信したメッセージを表示
                    message_type = message['type']
                    if message_type == 'status':
                        # キューに残っているタスク数を取得
                        queue_remaining = message['data']['status']['exec_info']['queue_remaining']
                        if queue_remaining == 0:
                            print("画像生成が完了しました")  # 画像生成が完了したら表示
                            break  # ループを終了
                    elif message_type == 'executing':
                        current_node = message['data']['node']
                elif isinstance(out, bytes) and current_node == '11':
                    print("画像データを受信しました") 
                    output_images.append(out[8:])
                    
        except asyncio.TimeoutError:
            print("タイムアウト: サーバーからの応答がありません")  # タイムアウト時のエラーメッセージ
            
    return output_images

# プロンプトをキューに追加する関数
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}# プロンプトを辞書形式で作成
    data = json.dumps(p).encode('utf-8')  # JSON形式にエンコード
    req = request.Request(f"https://{SERVER_ADDRESS}/prompt", data=data)  # POSTリクエストを作成
    response = request.urlopen(req, context=ssl_context)  # サーバーにリクエストを送信
    return response.read()  # レスポンスを返す

# メインプログラム
if __name__ == '__main__':
    # workflow_api.jsonファイルを読み込む
    with open(WORKFLOW_PATH, 'r') as file:
        prompt = json.load(file)  # JSON形式のデータを辞書として読み込む
    
    # プロンプトの内容を変更する例

    # CLIPTextEncodeノードのテキストを変更
    # ポジティブプロンプト
    prompt["6"]["inputs"]["text"] = "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,"
    # ネガティブプロンプト
    prompt["7"]["inputs"]["text"] = "text, watermark"

    # KSamplerノードのシードをランダムに設定
    prompt["3"]["inputs"]["seed"] = random.randint(1, 1000000)

    # プロンプトをキューに追加し、サーバーのレスポンスを取得
    response = queue_prompt(prompt)
    print('response: ' + str(response))  # サーバーからのレスポンスを表示
    
    # レスポンスをJSON形式の辞書に変換
    response_json = json.loads(response)

    # prompt_idをレスポンスから取得
    prompt_id = response_json.get('prompt_id', None)

    # 画像生成が完了するまでWebSocketで待機
    generated_images = asyncio.run(get_images(prompt_id))
    
    # 次の連番を取得
    num = get_next_image_number()
    
    # 取得した画像の情報をループで処理
    for image_data in generated_images:        
        # 画像をimagesフォルダ内に保存するパスを作成
        save_path = os.path.join('images', f"ComfyUI_{num}.png")

        # ローカルファイルに画像を書き込み（imagesフォルダ内）
        with open(save_path, 'wb') as file:
            file.write(image_data)
        
        # 次の連番に進める
        num += 1
