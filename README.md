# しおりノート

Python と Flet で作った、ブラウザで使える宿題管理アプリです。クラス・宿題・期限を登録し、完了状態の切り替えや、クラス別・状態別の絞り込みができます。期限が近い宿題や期限超過の件数も確認できます。

宿題データはユーザーのホームディレクトリにある `~/.daily_homework_tracker.json` に保存されます。

## 起動方法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

起動するとブラウザでアプリが開きます。完了済みの宿題をまとめて削除したり、作業中に音楽を再生したりできます。音楽と完了時の画像の表示にはインターネット接続が必要です。
