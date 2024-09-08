# ComfyUI APIを利用した画像生成のサンプルコード

このプロジェクトは、ComfyUIサーバーと連携して、プロンプトに基づいて画像を生成するスクリプトです。WebSocketを使用して画像生成の進行状況をリアルタイムで監視し、生成された画像をローカルの`images`フォルダにダウンロードします。プロンプトや設定は、`workflow_api.json`ファイルを通じて管理され、サーバーに送信されて処理が行われます。

## 機能

- ComfyUIサーバーに画像生成のプロンプトを送信
- WebSocketを介して画像生成の進行状況を監視
- 生成された画像をローカルの`images`フォルダに保存
- `workflow_api.json`ファイルを使用してワークフローを設定
- SSLを使用した安全なサーバー通信

## 前提条件

このスクリプトを実行する前に、以下の環境が整っていることを確認してください：

- Python 3.7以上
- 必要なPythonライブラリ（下記参照）

## インストール

1. **リポジトリをクローン**：
    ```bash
    git clone https://github.com/your-repository/comfyui-image-generator.git
    cd comfyui-image-generator
    ```

2. **依存関係をインストール**：
    必要なライブラリをpipでインストールします：
    ```bash
    pip install -r requirements.txt
    ```

    または、以下のコマンドで手動でインストールします：
    ```bash
    pip install websockets certifi asyncio
    ```

3. **ワークフローファイルの設定**：
    プロジェクトディレクトリに`workflow_api.json`ファイルを正しく配置してください。このファイルには、ComfyUIサーバー用のプロンプト設定が含まれています。

## 設定

スクリプトを実行する前に、以下の設定を確認してください：

- **ComfyUIサーバーのアドレス**：スクリプト内の`FQDN`変数を、使用しているComfyUIサーバーのFQDN（完全修飾ドメイン名）に更新します。
  
    ```python
    FQDN = "your-comfyui-server-address"
    ```

- **ワークフローファイル**：`workflow_api.json`ファイルが正しいフォーマットで配置されていることを確認してください。

## 使用方法

1. **スクリプトを実行**：

    メインスクリプトをPythonで実行します：
    ```bash
    python3 main.py
    ```

2. **プロンプトの変更（オプション）**：
    
    スクリプト内の以下の部分を編集することで、プロンプトやシード値を変更できます：
    
    ```python
    # プロンプトテキストを変更
    prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

    # シード値をランダムに設定
    prompt["3"]["inputs"]["seed"] = random.randint(1, 1000000)
    ```

3. **進行状況の監視**：

    スクリプトはWebSocketを使用して、画像生成の進行状況をリアルタイムで監視します。生成が完了すると、画像は`images`フォルダにダウンロードされます。

## 出力

- 生成された画像は、`images`フォルダ内に保存されます。ファイル名はサーバーのレスポンスに基づいて設定されます。
  
  画像情報はターミナルに表示されます：

  ```bash
  Filename: ComfyUI_00053_.png, Type: output, Subfolder: 
  ```

## エラーハンドリング

- **タイムアウト処理**：WebSocket接続が30秒以内に応答を受け取れない場合、タイムアウトエラーメッセージが表示されます。
  
  ```bash
  タイムアウト: サーバーからの応答がありません
  ```

- **SSLエラー**：SSL証明書の設定が正しく構成されていることを確認してください（`certifi`を使用）。
