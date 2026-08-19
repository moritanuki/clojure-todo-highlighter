# Theme override examples

## `settings.theme-overrides.jsonc`

次のテーマ用の設定例を含む。

- `Catppuccin Frappé - No Italics`
- `Catppuccin Frappé`
- `One Dark`
- `One Light`

Catppuccin Frappé系では、タグ文字だけを明るい `#c6d0f5` にし、タグ以外の通常コメント文字色 `#949cbb` は維持する。アクセント背景は12% alphaで重ねる。Frappé公式Zedテーマのwarning/error背景と同じ `0x1f` の濃さなので、暗いeditor背景 `#303446` から浮きすぎない。

- TODO: Flamingo `#eebebe1f`
- NOTE: Teal `#81c8be1f`
- FIXME: Red `#e782841f`
- WARN: Yellow `#e5c8901f`

テーマ名はZedのtheme selector表示と完全一致させる。現在の設定が `Catppuccin Frappé - No Italics` なら、同名blockを使い、`font_style` は `null` のままにする。

## `settings.custom-theme.template.jsonc`

任意テーマへ手動で追加する最小テンプレート。`YOUR EXACT THEME NAME` とhighlight tagの文字色を置き換える。

## generator

```bash
python3 scripts/generate_active_theme_overrides.py --appearance dark
```

generatorもCatppuccin Frappéテーマではタグ文字 `#c6d0f5`、Frappé palette、12% alphaを使う。使用中テーマ本来のstatus色を使う場合だけ、次を指定する。

```bash
python3 scripts/generate_active_theme_overrides.py \
  --appearance dark \
  --palette theme
```
