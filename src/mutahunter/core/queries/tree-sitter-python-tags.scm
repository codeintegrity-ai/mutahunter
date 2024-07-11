(class_definition
  name: (identifier) @name.definition.class) @definition.class

(function_definition
  name: (identifier) @name.definition.function) @definition.function

(call
  function: [
      (identifier) @name.reference.call
      (attribute
        attribute: (identifier) @name.reference.call)
  ]) @reference.call

;; For extreme mutation testing

;; Match if statements
(if_statement
  condition: (_) @condition
  consequence: (block) @consequence
  alternative: (block)? @alternative) @if_statement

;; Match for loops
(for_statement
  body: (block) @loop_body) @loop

;; Match while loops
(while_statement
  body: (block) @loop_body) @loop

;; Match return statements
(return_statement
  "return"
  (_)? @return_value) @return