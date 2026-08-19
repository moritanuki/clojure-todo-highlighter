; TODO Tag Highlighter
;
; The comment delimiter, colon, and body use the regular @comment capture.
; Only the tag label (name and optional owner) receives a category capture.
;
; IMPORTANT:
; These capture names are intentionally extension-specific. Common themes often
; define `comment.todo` as an orange foreground-only style. Reusing that name
; makes TODO text orange even when no background override is active. The unique
; `comment.todo_tag_highlighter.*` namespace avoids that collision.
;
; Zed resolves multiple captures right-to-left. When a matching theme override
; exists, the extension-specific capture is used. Otherwise it falls back to
; @comment and the complete comment remains normally styled.

; Tasks / follow-up work
((tag
  (prefix)? @comment
  (name) @comment @comment.todo_tag_highlighter.task
  ("(" @comment @comment.todo_tag_highlighter.task.owner
    (user) @comment @comment.todo_tag_highlighter.task.owner
    ")" @comment @comment.todo_tag_highlighter.task.owner)?
  ((prefix)? @comment
    (text)? @comment)*)
  (#match? @comment.todo_tag_highlighter.task "^(TODO|WIP|MAYBE|QUESTION|REVIEW|\\?)$"))

; Informational annotations
((tag
  (prefix)? @comment
  (name) @comment @comment.todo_tag_highlighter.info
  ("(" @comment @comment.todo_tag_highlighter.info.owner
    (user) @comment @comment.todo_tag_highlighter.info.owner
    ")" @comment @comment.todo_tag_highlighter.info.owner)?
  ((prefix)? @comment
    (text)? @comment)*)
  (#match? @comment.todo_tag_highlighter.info "^(NOTE|INFO|DOCS|PERF|TEST|IDEA|XXX|\\*)$"))

; Defects / must-fix annotations
((tag
  (prefix)? @comment
  (name) @comment @comment.todo_tag_highlighter.fix
  ("(" @comment @comment.todo_tag_highlighter.fix.owner
    (user) @comment @comment.todo_tag_highlighter.fix.owner
    ")" @comment @comment.todo_tag_highlighter.fix.owner)?
  ((prefix)? @comment
    (text)? @comment)*)
  (#match? @comment.todo_tag_highlighter.fix "^(FIXME|FIX|BUG|ERROR|DELETE|BROKEN|!)$"))

; Risks / warnings / temporary workarounds
((tag
  (prefix)? @comment
  (name) @comment @comment.todo_tag_highlighter.warning
  ("(" @comment @comment.todo_tag_highlighter.warning.owner
    (user) @comment @comment.todo_tag_highlighter.warning.owner
    ")" @comment @comment.todo_tag_highlighter.warning.owner)?
  ((prefix)? @comment
    (text)? @comment)*)
  (#match? @comment.todo_tag_highlighter.warning "^(HACK|WARNING|WARN|SAFETY|IMPORTANT|SECURITY|DEPRECATED|NOCOMMIT|#)$"))
