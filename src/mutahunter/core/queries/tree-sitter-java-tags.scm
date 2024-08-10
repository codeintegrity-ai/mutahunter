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

; Query to find method declarations annotated with @Test
(method_declaration
  (modifiers
    (marker_annotation
      name: (identifier) @annotation.test
      (#eq? @annotation.test "Test")))) @test.method

(method_declaration
  (modifiers
    (marker_annotation
      name: (identifier) @annotation.test
      (#eq? @annotation.test "ParameterizedTest")))) @test.method
