import array_type
import core_types
import syntax
import syntax_helpers
import tuple_type

from syntax_helpers import get_types
from transform import Transform

class RewriteTyped(Transform):
  def __init__(self, fn):
    Transform.__init__(self, fn, verify = False)
    self.fn_return_type = self.fn.type_env["$return"]

  def coerce_expr(self, expr, t):
    assert t is not None
    expr = self.transform_expr(expr)
    if expr.type == t:
      return expr
    elif isinstance(expr, syntax.Tuple):
      if not isinstance(t, tuple_type.TupleT) or \
          len(expr.type.elt_types) != t.elt_types:
        raise core_types.IncompatibleTypes(expr.type, t)
      else:
        new_elts = []
        for elt, elt_t in zip(expr.elts, t.elt_types):
          new_elts.append(self.coerce_expr(elt, elt_t))
        return syntax.Tuple(new_elts, type = t)
    else:
      assert \
          isinstance(expr.type, core_types.ScalarT) and \
          isinstance(t, core_types.ScalarT), \
          "Can't cast type %s into %s" % (expr.type, t)
      return self.cast(expr, t)

  def transform_merge(self, merge):
    new_merge = {}
    for (var, (left, right)) in merge.iteritems():
      t = self.type_env[var]
      new_left = self.coerce_expr(left, t)
      new_right = self.coerce_expr(right, t)
      new_merge[var] = (new_left, new_right)
    return new_merge

  def transform_lhs(self, lhs):
    if isinstance(lhs, syntax.Var):
      t = self.lookup_type(lhs.name)
      if t == lhs.type:
        return lhs
      else:
        return syntax.Var(lhs.name, type = t)
    elif isinstance(lhs, syntax.Tuple):
      elts = map(self.transform_lhs, lhs.elts)
      elt_types = get_types(elts)
      if elt_types != lhs.type.elt_types:
        return syntax.Tuple(elts, type = tuple_type.make_tuple_type(elt_types))
      else:
        return lhs
    else:
      return lhs

  def transform_Var(self, expr):
    expr.type = self.fn.type_env[expr.name]
    return expr

  def transform_PrimCall(self, expr):
      arg_types = get_types(expr.args)
      upcast_types = expr.prim.expected_input_types(arg_types)
      result_type = expr.prim.result_type(upcast_types)
      upcast_args = [self.coerce_expr(x, t)
                     for (x,t) in zip(expr.args, upcast_types)]
      return syntax.PrimCall(expr.prim, upcast_args, type = result_type)

  def transform_Array(self, expr):
    array_t = expr.type
    elt_t = array_t.elt_type
    assert array_t.rank > 0
    if array_t.rank == 1:
      new_elts = [self.coerce_expr(elt, elt_t) for elt in expr.elts]
      return syntax.Array(new_elts, type = array_t)
    else:
      # need to allocate an output array and copy the elements in
      first_elt = self.assign_temp(expr.elts[0], "first_elt")
      elt_dims = [self.shape(first_elt, i) for i in xrange(array_t.rank - 1)]
      n = len(expr.elts)
      outer_dim = syntax_helpers.const(n)
      all_dims = (outer_dim,) + tuple(elt_dims)
      array = self.alloc_array(elt_t, all_dims, "array_literal")
      for i, elt in enumerate(expr.elts):
        idx_expr = self.index(array, i, temp = False)
        # transform indexing to make missing indices explicit
        self.assign(idx_expr, expr.elts[i])
      return array

  def transform_Reduce(self, expr):
    acc_type = self.return_type(expr.combine)
    if expr.init and \
        not self.is_none(expr.init) and \
        expr.init.type != acc_type:
      expr.init = self.coerce_expr(expr.init, acc_type)

    return expr

  def transform_Scan(self, expr):
    acc_type = self.return_type(expr.combine)
    if expr.init and \
        not self.is_none(expr.init) and \
        expr.init.type != acc_type:
      expr.init = self.coerce_expr(expr.init, acc_type)
    return expr

  def transform_Slice(self, expr):
    # None step defaults to 1
    if isinstance(expr.step.type, core_types.NoneT):
      start_t = expr.start.type
      stop_t = expr.stop.type
      step = syntax_helpers.one_i64
      step_t = step.type
      slice_t = array_type.make_slice_type(start_t, stop_t, step_t)
      expr.step = step
      expr.type = slice_t
    return expr

  def transform_Assign(self, stmt):
    new_lhs = self.transform_lhs(stmt.lhs)
    lhs_t = new_lhs.type
    assert lhs_t is not None, "Expected a type for %s!" % stmt.lhs
    new_rhs = self.coerce_expr(stmt.rhs, lhs_t)
    assert new_rhs.type and isinstance(new_rhs.type, core_types.Type), \
        "Expected type annotation on %s, but got %s" % (new_rhs, new_rhs.type)
    stmt.lhs = new_lhs
    stmt.rhs = new_rhs
    return stmt

  def transform_If(self, stmt):
    stmt.cond = self.coerce_expr(stmt.cond, core_types.Bool)
    stmt.true = self.transform_block(stmt.true)
    stmt.false = self.transform_block(stmt.false)
    stmt.merge = self.transform_merge(stmt.merge)
    return stmt

  def transform_Return(self, stmt):
    stmt.value = self.coerce_expr(stmt.value, self.fn_return_type)
    return stmt

  def transform_While(self, stmt):
    stmt.cond = self.coerce_expr(stmt.cond, core_types.Bool)
    stmt.body = self.transform_block(stmt.body)
    stmt.merge = self.transform_merge(stmt.merge)
    return stmt

def rewrite_typed(typed_fundef):
  return RewriteTyped(typed_fundef).apply(copy=False)