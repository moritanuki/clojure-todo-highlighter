(ns demo.demo
  "TODO Tag Highlighter の Clojure 表示確認用ファイル")

;; TODO: ClinVar の取得処理をバッチ化する
;; TODO(api): レート制限時の指数バックオフを追加する
;; REVIEW: transcript version を無視する仕様を再確認する

;; NOTE: 通常は hg38 を利用し、入力に応じて hg19 へ切り替える
;; PERF: 同一 variant の annotation 結果をキャッシュする
;; IDEA: stale-while-revalidate を検討する

;; FIXME(parser): p.? を空文字列ではなく nil に正規化する
;; BUG: 複数 allele のとき VAF の対応がずれる
;; BROKEN: この分岐はサンプルデータで失敗する

;; HACK: upstream の修正が入ったら、この workaround を削除する
;; SECURITY: 患者 ID をログへ出さない
;; NOCOMMIT: デバッグ用の固定値を残さない

;; 通常コメント。タグ以外の文字色と style はこれと同じになる。
(defn annotate-variant
  [{:keys [gene protein-change] :as variant}]
  ;; TODO: 実際の annotation pipeline に置き換える
  (assoc variant
         :display-name (str gene " " protein-change)
         :status :pending))

(comment
  ;; セミコロンコメントなら、(comment ...) の内側でも対象になる
  (annotate-variant {:gene "FGF14" :protein-change "G118V"}))

#_(println "#_ reader discard 自体は対象外")
