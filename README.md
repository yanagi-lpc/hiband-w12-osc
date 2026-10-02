# hiband-w12-osc

HiBand W12 の心拍を、VRChat の OSC パラメータへ送る。

PC の Bluetooth をオンにする。スマホの専用アプリがウォッチに繋がっているときは切る。VRChat は Options の OSC をオンにする。

```text
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
hiband-w12-osc
```

既定の送り先は `127.0.0.1:9000` の `/avatar/parameters/HR`（整数）。`--osc-host`、`--osc-port`、`--address`、`--name` で変えられる。

起動すると、見つかるまで `scanning W12` と出る。時刻合わせのあと、BPM が変わるたびに `bpm 76` のように出る。最初の数字まで約 9 秒かかる。止めるのは Ctrl+C。
