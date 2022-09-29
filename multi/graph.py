import matplotlib.pyplot as plt
import base64
from io import BytesIO


def output_graph():                     # プロットしたグラフを画像データとして出力するための関数
    buffer = BytesIO()                   # バイナリI/O(画像や音声データを取り扱う際に利用)
    plt.savefig(buffer, format="png")    # png形式の画像データを取り扱う
    buffer.seek(0)                       # ストリーム先頭のoffset byteに変更
    img = buffer.getvalue()            # バッファの全内容を含むbytes
    graph = base64.b64encode(img)        # 画像ファイルをbase64でエンコード
    graph = graph.decode("utf-8")        # デコードして文字列から画像に変換
    buffer.close()
    return graph


# グラフをプロットするための関数
def plot_graph(x, y):
    plt.switch_backend("AGG")        # スクリプトを出力させない
    # plt.figure(figsize=(10, 5))       # グラフサイズ
    # plt.plot(x, y, linewidth=4)                     # グラフ作成
    # plt.rcParams["font.size"] = 15
    # plt.xticks(rotation=45)          # X軸値を45度傾けて表示
    # plt.ylabel("Rating")             # yラベル
    # plt.tight_layout()               # レイアウト
    fig = plt.figure(figsize=(10, 5))  # figureオブジェクトを作成
    ax = fig.add_subplot(1, 1, 1) # figに属するAxesオブジェクトを作成
    ax.set_title("Rating")
    ax.set_facecolor((0.95, 0.95, 0.95, 1))
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params('x', length=0, which='major')
    ax.tick_params('y', length=0, which='major')
    ax.grid(color="white")
    ax.plot(x, y, '-o')
    graph = output_graph()           # グラフプロット
    return graph
