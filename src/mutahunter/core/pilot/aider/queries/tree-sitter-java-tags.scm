(class_declaration
  name: (identifier) @name.definition.class) @definition.class

(method_declaration
  name: (identifier) @name.definition.method) @definition.method

(method_invocation
  name: (identifier) @name.reference.call
  arguments: (argument_list) @reference.call)

(interface_declaration
  name: (identifier) @name.definition.interface) @definition.interface

(type_list
  (type_identifier) @name.reference.implementation) @reference.implementation

(object_creation_expression
  type: (type_identifier) @name.reference.class) @reference.class

(superclass (type_identifier) @name.reference.class) @reference.class

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

;; Match do-while loops
(do_statement
  body: (block) @loop_body) @loop

(return_statement
  "return"
  (_)? @return_value) @return
