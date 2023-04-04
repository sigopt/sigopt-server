#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import ast
import io
import os
import tokenize

from zigopt.common.lists import find, generator_to_safe_iterator


# customlint: disable=AccidentalFormatStringRule


def find_parent_function(node):
  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
    return node
  else:
    if node.parent:
      return find_parent_function(node.parent)
    return None


class LintNodeRule(object):
  def check_node(self, node):
    raise NotImplementedError()


class ProhibitedMethodsRule(LintNodeRule):
  def __init__(self, prohibited_methods):
    self.prohibited_methods = prohibited_methods

  def is_prohibited_method_call(self, node):
    return (
      isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in self.prohibited_methods
    )


class AvoidDatetimeNowRule(ProhibitedMethodsRule):
  def __init__(self):
    super().__init__(prohibited_methods={"now", "utcnow"})

  def check_node(self, node):
    if (
      self.is_prohibited_method_call(node)
      and isinstance(node.func.value, ast.Attribute)
      and node.func.value.attr in ("dt", "datetime")
    ):
      return f"Prefer `current_datetime` to `datetime.{node.func.attr}` to ensure consistent use of UTC timezone"
    return None


class SafeRecursiveRule(LintNodeRule):
  def is_recursive_call(self, node, parent_function):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
      return parent_function and parent_function.name == node.func.id
    return None

  def check_node(self, node):
    if isinstance(node, ast.Call):
      parent_function = find_parent_function(node)
      if self.is_recursive_call(node, parent_function):
        defined_args = parent_function.args
        assert not defined_args.vararg, "Linting for recursive calls with *args is not supported"
        assert not defined_args.kwarg, "Linting for recursive calls with **kwargs is not supported"
        assert not defined_args.kwonlyargs, "Linting for recursive calls with keyword-only args is not supported"
        if len(defined_args.args) != (len(node.args) + len(node.keywords)):
          return "Recursive call appears to be missing arguments. Specify all arguments for recursive calls."
    return None


class SafeIteratorRule(LintNodeRule):
  def __init__(self, prohibited_iterators):
    self.prohibited_iterators = prohibited_iterators

  def is_iterator(self, node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.prohibited_iterators

  def check_node(self, node):
    if isinstance(node, ast.Return):
      if self.is_iterator(node.value):
        return (
          f"returning `{node.value.func.id}` is not allowed, suggest using `yield from` syntax "
          "or returning `zigopt.common.lists.safe_iterator`"
        )
    elif isinstance(node, ast.BinOp):
      if isinstance(node.op, ast.Add) and (self.is_iterator(node.left) or self.is_iterator(node.right)):
        return "adding iterators is not allowed"
    return None


class ProtobufMethodsRule(ProhibitedMethodsRule):
  def __init__(self):
    super().__init__(prohibited_methods={"MergeFrom", "CopyFrom"})

  def check_node(self, node):
    if self.is_prohibited_method_call(node):
      return (
        f"Do not call `{node.func.attr}` on protobufs - prefer the safer `{node.func.attr}` in zigopt.protobuf.lib`"
      )
    return None


class SafeYieldRule(LintNodeRule):
  def get_decorator_name(self, node):
    if isinstance(node, ast.Attribute):
      return node.attr
    if isinstance(node, ast.Name):
      return node.id
    assert isinstance(node, ast.Call)
    return self.get_decorator_name(node.func)

  def has_return_with_value(self, node):
    """
        Forbid including `yield` and `return value` in the same function.
        This construct is unlikely to behave as expected, since `return value` manifests
        as a `raise StopIteration(value)` in such a case. See https://stackoverflow.com/q/28806583/139544

        Since this is unlikely to behave as expected, and can be easily reproduced in more
        explicit language, forbid this construct.
        """
    return bool(find(ast.walk(node), lambda x: isinstance(x, ast.Return) and x.value))

  def missing_decorator(self, node):
    """
        Forbid including `yield` without a decorator that makes its usage safe.

        Reusing generators can cause confusing behaviour:

        def gen():
          for i in range(4):
            yield i
        x = gen()
        list(x) == [1,2,3,4]
        list(x) == []  # !?

        Avoid this by requiring usage of a decorator that makes usage safer for downstream callers. One of:
        - `generator_to_list` / `generator_to_dict`, which makes the function return an instead of a generator
          (for example, `generator_to_list` would fix the above so that the second line will be `list(x) == [1,2,3,4]`)
        - `generator_to_safe_iterator`, which wraps the generator in a `safe_iterator` (so that the second line
          will throw)
        """
    protects_iterator = lambda decorator: self.get_decorator_name(decorator) in (
      "generator_to_list",
      "generator_to_dict",
      "generator_to_safe_iterator",
      # Marker to allow opting in to typical behavior.
      # TODO(SN-1145): Make this a comment that allows custom lint rules to be disabled
      "unsafe_generator",
      # Third-party decorators that use `yield`s to manage control flow
      "contextmanager",
      "fixture",
      "hookimpl",
    )
    return not bool(find(node.decorator_list, protects_iterator))

  def check_node(self, node):
    if isinstance(node, (ast.Yield, ast.YieldFrom)):
      function_node = find_parent_function(node)
      if self.has_return_with_value(function_node):
        return "Do not mix `return value` and `yield` in the same function"
      if self.missing_decorator(function_node):
        return "Functions with `yield` should be decorated with a `generator_to_X` function"
    return None


class TrailingCommaRule(LintNodeRule):
  def check_node(self, node):
    if isinstance(
      node,
      (
        ast.Assign,
        ast.AugAssign,
        ast.Expr,
        ast.Return,
        ast.Yield,
      ),
    ) and isinstance(node.value, ast.Tuple):
      if len(node.value.elts) == 1:
        return "Prefer `tuple` for single-element tuples"
    return None


class FormatStringRule(ProhibitedMethodsRule):
  def __init__(self):
    super().__init__(prohibited_methods={"format"})

  def check_node(self, node):
    if self.is_prohibited_method_call(node) and isinstance(node.func.value, (ast.Str, ast.JoinedStr)):
      return "use formatted string literals instead of str.format"
    return None


class AccidentalFormatStringRule(LintNodeRule):
  def check_node(self, node):
    if isinstance(node, ast.Str) and "{" in node.s and "}" in node.s:
      # pylint: disable=f-string-without-interpolation
      return f"{{}} detected in string constant, did you forget `f`?"  # noqa: F541
      # pylint: enable=f-string-without-interpolation
    return None


class AddingStringsRule(LintNodeRule):
  def check_node(self, node):
    if (
      isinstance(node, ast.BinOp)
      and isinstance(node.left, (ast.Str, ast.JoinedStr, ast.FormattedValue))
      and isinstance(node.right, (ast.Str, ast.JoinedStr, ast.FormattedValue))
    ):
      return "use parenthesis instead of addition for long strings"
    return None


class EmptySuperRule(LintNodeRule):
  def check_node(self, node):
    if (
      isinstance(node, ast.Call)
      and isinstance(node.func, ast.Name)
      and node.func.id == "super"
      and (node.args or node.keywords)
    ):
      return "call to super() should have no arguments"
    return None


class GeneratorExpressionRule(LintNodeRule):
  invalid_builtins = (
    "map",
    "filter",
  )

  def check_node(self, node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
      if node.func.id in self.invalid_builtins:
        return f"use generator expression over the {node.func.id} function"
    return None


class ForbidTestSuiteInheritanceRule(LintNodeRule):
  def check_node(self, node):
    if isinstance(node, (ast.ClassDef)):
      prefix = "Test"
      if node.name.startswith(prefix):
        for base in node.bases:
          if isinstance(base, ast.Name):
            if base.id.startswith(prefix):
              return (
                f"Inheriting the test suite {base.id} may cause it to get run twice."
                f" Classes beginning with `{prefix}` are interpreted by pytest as test suites."
              )
    return None


class ForbidImportTestSuiteRule(LintNodeRule):
  def check_node(self, node):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
      for alias in node.names:
        name = alias.asname or alias.name
        for prefix in ("Test", "test_"):
          if name.startswith("Test") or name.startswith("test_"):
            return (
              f"Importing the test suite {name} may cause it to get run twice."
              f" Imported objects beginning with `{prefix}` are interpreted by pytest as test suites."
            )
    return None


class SetComparisonRule(LintNodeRule):
  invalid_ops = (
    ast.Lt,
    ast.Gt,
    ast.LtE,
    ast.GtE,
  )

  def is_comprehended_set(self, node):
    if isinstance(node, ast.SetComp):
      return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "set":
      for arg_node in node.args:
        if isinstance(arg_node, (ast.GeneratorExp, ast.ListComp)):
          return True
    return False

  def check_node(self, node):
    if isinstance(node, ast.Compare):
      comparators = [node.left] + node.comparators
      ops = node.ops
      if len(comparators) > 1:
        for left, right, op in zip(comparators[:-1], comparators[1:], ops):
          if any(isinstance(op, invalid_op) for invalid_op in self.invalid_ops) and (
            self.is_comprehended_set(left) or self.is_comprehended_set(right)
          ):
            return "use any() and all() over comprehended set comparisons"
    return None


class NoImportLibsigoptComputeRule(LintNodeRule):
  def check_node(self, node):
    error_msg = (
      "Should not import from libsigopt.compute, consider moving the class/method to libsigopt.aux or libsigopt.views"
    )
    if isinstance(node, ast.Import):
      for name in node.names:
        if name.name == "libsigopt.compute":
          return error_msg
    if isinstance(node, ast.ImportFrom):
      if node.module.startswith("libsigopt.compute"):
        return error_msg
    return None


def prepare_all_lint_node_rules(source, filename):
  rules = [
    AccidentalFormatStringRule(),
    AddingStringsRule(),
    EmptySuperRule(),
    ForbidImportTestSuiteRule(),
    ForbidTestSuiteInheritanceRule(),
    FormatStringRule(),
    GeneratorExpressionRule(),
    ProtobufMethodsRule(),
    SafeIteratorRule({"range", "zip", "map", "filter"}),
    SafeRecursiveRule(),
    SafeYieldRule(),
    SetComparisonRule(),
    TrailingCommaRule(),
    NoImportLibsigoptComputeRule(),
  ]
  if os.path.split(filename)[:3] == ["src", "python", "zigopt"]:
    rules.extend(
      [
        AvoidDatetimeNowRule(),
      ]
    )
  return rules


@generator_to_safe_iterator
def get_problems(tree, rules, disables):
  tree.parent = None
  for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
      child.parent = node
    for rule in rules:
      rule_name = rule.__class__.__name__
      if hasattr(node, "lineno") and rule_name in disables and disables[rule_name] <= node.lineno:
        continue
      problem = rule.check_node(node)
      if problem:
        yield problem, node


@generator_to_safe_iterator
def check_file(source_name):
  with open(source_name, "r") as source_file:
    raw_source = source_file.read()
  rules = prepare_all_lint_node_rules(raw_source, source_name)

  disables = {}
  tokens = list(tokenize.tokenize(io.BytesIO(raw_source.encode()).readline))
  for tk in tokens:
    disable_marker = "customlint: disable="
    enable_marker = "customlint: enable="
    if tk.type == tokenize.COMMENT:
      if enable_marker in tk.string:
        raise Exception("Re-enabling customlint disables is not supported")
      if disable_marker in tk.string:
        comment_suffix = tk.string[tk.string.find(disable_marker) + len(disable_marker) :]
        rule_names = [r.strip() for r in comment_suffix.split(",")]
        for rule_name in rule_names:
          lineno = tk.start[0]
          disables[rule_name] = disables.get(rule_name, lineno)

  tree = ast.parse(raw_source, source_name)
  problems = sorted(get_problems(tree, rules, disables), key=lambda p: (p[1].lineno, p[1].col_offset))
  for message, node in problems:
    yield f"{source_name}:{node.lineno}:{node.col_offset}: {message}"


if __name__ == "__main__":
  import argparse
  import subprocess
  import sys

  parser = argparse.ArgumentParser(description="Custom lint rules for python")
  parser.add_argument("source_names", nargs="*", help="Sources to check (default to `git ls-files '*.py'`)")
  args = parser.parse_args()
  if args.source_names:
    source_names = args.source_names
  else:
    source_names = (
      e for e in subprocess.check_output(["git", "ls-files", "*.py"]).decode("utf-8").split("\n") if len(e)
    )
  problems = False
  for source_name in source_names:
    for message in check_file(source_name):
      problems = True
      print(message)  # noqa: T001
  sys.exit(int(problems))
