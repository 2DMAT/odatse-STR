ベイズ最適化
=====================================

ここでは、ベイズ最適化を行い、回折データから原子座標を解析する方法について説明します。
ベイズ最適化には `PHYSBO <https://www.pasums.issp.u-tokyo.ac.jp/physbo>`_ を用いています。
グリッド探索と同様に、探索グリッドを与えるデータ ``MeshData.txt`` を事前に準備する必要があります。

サンプルファイルの場所
~~~~~~~~~~~~~~~~~~~~~~~~

サンプルファイルは ``sample/single_beam/bayes`` にあります。
フォルダには以下のファイルが格納されています。

- ``bulk.txt``

  ``bulk.exe`` の入力ファイル

- ``experiment.txt``, ``template.txt``

  メインプログラムでの計算を進めるための参照ファイル

- ``MeshData.txt``

  探索グリッドのデータ

- ``ref_BayesData.txt``

  計算が正しく実行されたか確認するためのリファレンスファイル

- ``input.toml``

  メインプログラムの入力ファイル

- ``prepare.sh`` , ``do.sh``

  本チュートリアルを一括計算するために準備されたスクリプト

以下、これらのファイルについて説明したあと、実際の計算結果を紹介します。

参照ファイルの説明
~~~~~~~~~~~~~~~~~~~

``template.txt``, ``experiment.txt`` については、Nelder-Mead法による最適化と同じものを使用します。
ただし、計算を軽くするため ``value_03`` は用いずに ``3.5`` に固定し、2次元のグリッド探索を行うように変更してあります。
実際に探索するグリッドは ``MeshData.txt`` で与えます。
サンプルでは ``MeshData.txt`` の中身は以下のようになっています。

.. code-block::

  1 3.5 3.5
  2 3.6 3.5
  3 3.6 3.6
  4 3.7 3.5
  5 3.7 3.6
  6 3.7 3.7
  7 3.8 3.5
  8 3.8 3.6
  9 3.8 3.7
  10 3.8 3.8
    ...

1列目が通し番号、2列目以降は ``template.txt`` に入る ``value_0`` , ``value_1`` の値が順に指定されています。

入力ファイルの説明
~~~~~~~~~~~~~~~~~~~

ここでは、メインプログラム用の入力ファイル ``input.toml`` について説明します。
``input.toml`` の詳細については入力ファイルに記載されています。
以下は、サンプルファイルにある ``input.toml`` の内容です。

.. code-block::

    [base]
    dimension = 2
    output_dir = "output"

    [solver]
    name = "sim-trhepd-rheed"
    run_scheme = "subprocess"
    generate_rocking_curve = false

    [solver.config]
    cal_number = [1]

    [solver.param]
    string_list = ["value_01", "value_02" ]

    [solver.reference]
    path = "experiment.txt"
    exp_number = [1]

    [algorithm]
    name = "bayes"
    label_list = ["z1", "z2"]
    seed = 1

    [algorithm.param]
    mesh_path = "MeshData.txt"

    [algorithm.bayes]
    random_max_num_probes = 10
    bayes_max_num_probes = 20


最初に ``[base]`` セクションについて説明します。

- ``dimension`` は最適化したい変数の個数で、今の場合は ``template.txt`` で説明したように2つの変数の最適化を行うので、 ``2`` を指定します。

- ``output_dir`` は出力先のディレクトリ名です。省略した場合はプログラムを実行したディレクトリになります。
  
``[solver]`` セクションではメインプログラムの内部で使用するソルバーとその設定を指定します。

- ``name`` は使用したいソルバーの名前です。 ``sim-trhepd-rheed`` に固定されています。

- ``run_scheme`` はソルバーを実行する方法の指定です。 ``subprocess`` のみ指定可能です。

ソルバーの設定は、サブセクションの ``[solver.config]``, ``[solver.param]``, ``[solver.reference]``, ``[solver.post]`` で行います。

``[solver.config]`` セクションではメインプログラム内部で呼び出す ``surf.exe`` により得られた出力ファイルを読み込む際のオプションを指定します。

- ``cal_number`` は出力ファイルの何列目を読み込むかを指定します。

``[solver.param]`` セクションではメインプログラム内部で呼び出す ``surf.exe`` への入力パラメータについてのオプションを指定します。

- ``string_list`` は、 ``template.txt`` で読み込む、動かしたい変数の名前のリストです。

``[solver.reference]`` セクションでは、実験データの置いてある場所と読みこむ範囲を指定します。

- ``path`` は実験データが置いてあるパスを指定します。

- ``exp_number`` は実験データファイルの何列目を読み込むかを指定します。

``[solver.post]`` セクションでは、後処理のオプションを指定します。

- ``normalization`` は複数ビームの規格化を指定します。

``[algorithm]`` セクションでは、使用するアルゴリスムとその設定をします。

- ``name`` は使用したいアルゴリズムの名前で、このチュートリアルでは、ベイズ最適化による解析を行うので、 ``bayes`` を指定します。

- ``label_list`` は、 ``value_0x`` (x=1,2) を出力する際につけるラベル名のリストです。

``[algorithm.param]`` セクションで、探索パラメータを設定します。

- ``mesh_path`` はメッシュファイルへのパスを設定します。

``[algorithm.bayes]`` セクションでは、ベイズ最適化のハイパーパラメータを設定します。

- ``random_max_num_probes`` は、ベイズ最適化を行う前のランダム探索する回数を指定します。

- ``bayes_max_num_probes`` は、ベイズ探索を行う回数を指定します。

その他、入力ファイルで指定可能なパラメータの詳細については入力ファイルの章をご覧ください。

計算実行
~~~~~~~~~~~~

最初にサンプルファイルが置いてあるフォルダへ移動します(以下、本ソフトウェアをダウンロードしたディレクトリ直下にいることを仮定します).

.. code-block::

    $ cd sample/single_beam/bayes

順問題の時と同様に、 ``bulk.exe`` と ``surf.exe`` をコピーします。

.. code-block::

    $ cp ../../sim-trhepd-rheed/src/bulk.exe .
    $ cp ../../sim-trhepd-rheed/src/surf.exe .

最初に ``bulk.exe`` を実行し、 ``bulkP.b`` を作成します。

.. code-block::

    $ ./bulk.exe

そのあとに、メインプログラムを実行します(計算時間は通常のPCで数秒程度で終わります)。

.. code-block::

    $ odatse-STR input.toml | tee log.txt

実行すると以下の様な標準出力がされます。

.. code-block::

    # parameter
    random_max_num_probes = 10
    bayes_max_num_probes = 20
    score = TS
    interval = 5
    num_rand_basis = 5000
    name            : bayes
    label_list      : ['z1', 'z2']
    seed            : 1
    param.mesh_path : ./MeshData.txt
    bayes.random_max_num_probes: 10
    bayes.bayes_max_num_probes: 20
    0001-th step: f(x) = -0.037237 (action=150)
       current best f(x) = -0.037237 (best action=150) 

    0002-th step: f(x) = -0.060508 (action=36)
       current best f(x) = -0.037237 (best action=150) 

    0003-th step: f(x) = -0.062158 (action=175)
       current best f(x) = -0.037237 (best action=150) 

    0004-th step: f(x) = -0.049211 (action=85)
       current best f(x) = -0.037237 (best action=150) 

    0005-th step: f(x) = -0.083945 (action=255)
       current best f(x) = -0.037237 (best action=150) 

    0006-th step: f(x) = -0.055569 (action=170)
       current best f(x) = -0.037237 (best action=150) 
    ...

最初に設定したパラメータのリスト、そのあとに各ステップでの候補パラメータと、その時の ``R-factor`` に ``-1`` を乗じた ``f(x)`` が出力されます。また、その時点での一番良いスコアを持つグリッドインデックス (``action``) とその場合の ``f(x)`` と変数が出力されます。
出力ディレクトリ ``output/0/`` の下には更にグリッドのidがついたサブフォルダ ``LogXXXX_00000000``  (``XXXX`` がグリッドのid)が作成され、ソルバーの出力が保存されます。
(``MeshData.txt`` に付けられた番号がグリッドのidとして割り振られます。)
最終的に推定されたパラメータは ``output/BayesData.txt`` に出力されます。

今回の場合は

.. code-block::

  #step z1 z2 fx z1_action z2_action fx_action
  0 5.1 4.9 0.037237314010261195 5.1 4.9 0.037237314010261195
  1 5.1 4.9 0.037237314010261195 4.3 3.5 0.06050786306685965
  2 5.1 4.9 0.037237314010261195 5.3 3.9 0.06215778000834068
  3 5.1 4.9 0.037237314010261195 4.7 4.2 0.049210767760634364
  4 5.1 4.9 0.037237314010261195 5.7 3.7 0.08394457854191653
  5 5.1 4.9 0.037237314010261195 5.2 5.2 0.05556857782716691
  6 5.1 4.9 0.037237314010261195 5.7 4.0 0.0754639895013157
  7 5.1 4.9 0.037237314010261195 6.0 4.4 0.054757310814479355
  8 5.1 4.9 0.037237314010261195 6.0 4.2 0.06339787375966344
  9 5.1 4.9 0.037237314010261195 5.7 5.2 0.05348404677676544
  10 5.1 4.7 0.03002813055356341 5.1 4.7 0.03002813055356341
  11 5.1 4.7 0.03002813055356341 5.0 4.4 0.03019977423448576
  12 5.3 4.5 0.02887504880071686 5.3 4.5 0.02887504880071686
  13 5.1 4.5 0.025865346123665988 5.1 4.5 0.025865346123665988
  14 5.2 4.4 0.02031077875240244 5.2 4.4 0.02031077875240244
  15 5.2 4.4 0.02031077875240244 5.2 4.6 0.023291891689059388
  16 5.2 4.4 0.02031077875240244 5.2 4.5 0.02345999725278686
  17 5.2 4.4 0.02031077875240244 5.1 4.4 0.022561543431398066
  18 5.2 4.4 0.02031077875240244 5.3 4.4 0.02544527153306051
  19 5.2 4.4 0.02031077875240244 5.1 4.6 0.02778877135528466
  20 5.2 4.3 0.012576357659158034 5.2 4.3 0.012576357659158034
  21 5.1 4.2 0.010217361468113488 5.1 4.2 0.010217361468113488
  22 5.1 4.2 0.010217361468113488 5.2 4.2 0.013178053637167673
    ...

のように得られます。1列目にステップ数、2列目、3列目、4列目にその時点での最高スコアを与える
``value_01``, ``value_02`` と ``R-factor`` が記載されます。
続けて、そのステップで候補となった ``value_01``, ``value_02`` と ``R-factor`` が記載されます。
今回の場合は21ステップ目で正しい解が得られていることがわかります。

なお、一括計算するスクリプトとして ``do.sh`` を用意しています。
``do.sh`` では ``BayesData.dat`` と ``ref_BayesData.dat`` の差分も比較しています。
以下、説明は割愛しますが、その中身を掲載します。

.. code-block::

    #!/bin/sh

    sh prepare.sh

    ./bulk.exe

    time odatse-STR input.toml

    echo diff output/BayesData.txt ref_BayesData.txt
    res=0
    diff output/BayesData.txt ref_BayesData.txt || res=$?
    if [ $res -eq 0 ]; then
      echo TEST PASS
      true
    else
      echo TEST FAILED: BayesData.txt.txt and ref_BayesData.txt.txt differ
      false
    fi

計算結果の可視化
~~~~~~~~~~~~~~~~~~~

``BayesData.txt`` を参照することで、何ステップ目のパラメータが最小スコアを与えたかがわかります。
``[solver]`` セクションの ``generate_rocking_curve`` パラメータを ``true`` にすると、
各ステップ毎のサブフォルダに ``RockingCurve_calculated.txt`` が格納されます。
Nelder-Mead法による最適化での手順に従い、実験値との比較を行うことが可能です。
