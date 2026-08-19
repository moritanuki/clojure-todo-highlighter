# Changelog

## 0.3.3

- Catppuccin Frappéのタグ文字色を、通常コメント色 `#949cbb` から明るいText色 `#c6d0f5` へ変更。
- コメント記号・コロン・本文は通常コメント色のまま維持。
- 背景色は12% alphaのFrappé paletteを維持。
- 設定generatorにタグ文字色の個別指定を追加。
- `demo/demo.clj` のnamespaceをfile pathに合わせ、Clojure LSPのnamespace mismatchを解消。

## 0.3.2 — 2026-08-20

- Catppuccin Frappéのdark editor背景 `#303446` に合わせ、background alphaを20%から12%（`0x1f`）へ調整。
- TODO/task `#eebebe1f`、NOTE/info `#81c8be1f`、FIXME/fix `#e782841f`、WARN/warning `#e5c8901f` に変更。
- 現在使用中の正確なtheme名 `Catppuccin Frappé - No Italics` 用presetを追加。
- No Italics版では通常コメント色 `#949cbb` と `font_style: null` を維持。
- active-theme generatorのbundled metadataへNo Italics版を追加し、default alphaを12%へ変更。
- README、HTML guide、設定例、demoをdark-mode presetへ更新。

## 0.3.1 — 2026-08-20

- 背景paletteをCatppuccin Frappé系へ変更。
- TODO/taskはFlamingo、NOTE/infoはTeal、FIXME/fixはRed、WARN/warningはYellowを使用。
- Catppuccin Frappé用の正確な通常コメントstyle（`#949cbb` / italic）を設定例へ追加。
- generatorのdefault paletteをCatppuccin Frappé、default alphaを20%へ変更。
- `--palette theme` を追加し、使用中テーマ固有のstatus色へ切り替えられるようにした。
- HTML generatorとREADME demoをCatppuccin Frappé基調へ更新。

## 0.3.0 — 2026-08-19

- `comment.todo` など既存テーマと衝突しやすいcapture名を廃止。
- captureを `comment.todo_tag_highlighter.*` というextension固有namespaceへ変更。
- 背景設定が未適用のときは、オレンジ文字ではなく通常の `comment` styleへ確実にフォールバックするよう修正。
- One Dark / One Lightの設定例を、不透明で判別しやすく、通常コメント文字とのコントラストも取りやすい背景色へ変更。
- 使用中テーマをsettingsから検出してoverrideを生成する `generate_active_theme_overrides.py` を追加。
- カスタムテーマ用テンプレートと、HTML内の設定generator / previewを追加。
- READMEとトラブルシューティングを、確認された「文字色だけ変わる」症状に合わせて更新。

## 0.2.0 — 2026-08-19

- extension名とIDをClojure固有から `TODO Tag Highlighter` へ変更。
- Clojure以外の主要言語で使えることをREADME・demo・HTMLに反映。
- コメント全体ではなく、タグ名と任意のowner部分だけをcategory captureに変更。
- コメント記号、コロン、本文を通常の `comment` captureに変更。
- `comment.todo` / `comment.info` / `comment.error` / `comment.warn` の背景色設定例を追加。
- One Dark / One Light用の設定例を追加。
- 任意テーマから通常コメントstyleを引き継ぐgeneratorを追加。
- 複数言語のdemoファイルと更新版demo画像を追加。

## 0.1.0 — 2026-08-19

- Clojureのセミコロンコメントに対するタスクタグ強調を追加。
- `TODO` / `NOTE` / `FIXME` / `HACK` 系の4カテゴリを追加。
- ローカル導入用README、Clojure demo、テーマ上書き例を追加。
- ローカル利用と公開手順を分けたHTML guideを追加。
