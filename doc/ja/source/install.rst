odatse-STR のインストール
================================================================

実行環境・必要なパッケージ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- python 3.9 以上

    - 必要なpythonパッケージ

        - tomli (>= 1.2)
        - numpy (>= 1.14)

- ODAT-SE version 3.0 以降

- sim-trhepd-rheed version 1.0.2 以降


ダウンロード・インストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. ODAT-SE をインストールする

   - ソースコードからのインストール

     リポジトリから ODAT-SE のソースファイルを取得します。

     .. code-block:: bash

	$ git clone https://github.com/issp-center-dev/ODAT-SE.git

     pip コマンドを実行してインストールします。

     .. code-block:: bash

	$ cd ODAT-SE
	$ python3 -m pip install .

	
     ``--user`` オプションを付けるとローカル (``$HOME/.local``) にインストールできます。
	    
     ``python3 -m pip install .[all]`` を実行するとオプションのパッケージも同時にインストールします。
	  
2. sim-trhepd-rheed をインストールする

   - 公式サイトからソースパッケージをダウンロードします。

     https://github.com/sim-trhepd-rheed/sim-trhepd-rheed/releases/tag/v1.0.2
     
     .. code-block:: bash

	$ wget -O sim-trhepd-rheed-1.0.2.tar.gz https://github.com/sim-trhepd-rheed/sim-trhepd-rheed/archive/refs/tags/v1.0.2.tar.gz

   - ソースパッケージを展開し、コンパイルします。必要に応じて sim-trhepd-rheed/src 内の Makefile を編集してください。
	
     .. code-block:: bash

	$ tar xvfz sim-trhepd-rheed-1.0.2.tar.gz
	$ cd sim-trhepd-rheed-1.0.2/src
	$ make

     実行形式 ``bulk.exe``, ``surf.exe``, ``potcalc.exe``, ``xyz.exe`` が作成されます。
     ``bulk.exe`` と ``surf.exe`` を PATH の通ったディレクトリ (環境変数 PATH に列挙された、実行プログラムを探索するディレクトリ) に配置するか、実行時にディレクトリ名をつけて指定します。

3. odatse-STR をインストールする

   - ソースコードからのインストール

     odatse-STR のソースファイルは GitHub リポジトリから取得できます。以下の手順でリポジトリをクローンした後、pip コマンドを実行してインストールします。

     .. code-block:: bash

        $ git clone https://github.com/2DMAT/odatse-STR.git
	$ cd odatse-STR
	$ python3 -m pip install .

     ``--user`` オプションを付けるとローカル (``$HOME/.local``) にインストールできます。
	    
     odatse-STR のライブラリと、実行コマンド ``odatse-STR`` がインストールされます。


実行方法
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ODAT-SE では順問題ソルバと逆問題解析アルゴリズムを組み合わせて解析を行います。
TRHEPDの解析を行うには次の2通りの方法があります。

1. このパッケージに含まれる odatse-STR プログラムを利用して解析を行います。ユーザは、プログラムの入力となるパラメータファルを TOML 形式で作成し、プログラムの引数に指定してコマンドを実行します。逆問題解析のアルゴリズムはパラメータで選択できます。

2. odatse-STR ライブラリと ODAT-SE フレームワークを用いてプログラムを作成し、解析を行います。逆問題解析アルゴリズムは import するモジュールで選択します。プログラム中に入力データの生成を組み込むなど、柔軟な使い方ができます。

パラメータの種類やライブラリの利用方法については以降の章で説明します。


アンインストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

odatse-STR モジュールおよび ODAT-SE モジュールをアンインストールするには、以下のコマンドを実行します。

.. code-block:: bash

    $ python3 -m pip uninstall odatse-STR ODAT-SE
