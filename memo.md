# 2022/4/8

- 部品の実装
  - PCTL -> multiquatexへの変換
  - PRISMが出力する反例ファイルの解析
  - MultiVeStAの呼び出しと結果の処理

- 処理の流れ(BBCの一回のループ)
  - AALpyでMDPを学習して、PRISMのモデルフォーマットでファイル出力(mdp.prism)
  - PRISMで、mdp.prismとPCTLの仕様でモデル検査
    - オプションとして '-exportadvmdp' をつけて反例ファイル(adv.tra)を出力させる
  - adv.traを読み込んで、各状態に対するアクションを決める
    - ブラックボックスなMDPなので、
  - MDP

```flow
s=>start: start
learn=>operation: AALpy

```

