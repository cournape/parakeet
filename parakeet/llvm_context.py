import config
import llvm.core as core
import llvm.ee as ee
import llvm.passes as passes

class LLVM_Context:
  """Combine a module, exec engine, and pass manager into a single object"""

  _verify_passes = [
    'preverify',
    'domtree',
    'verify'
  ]

  _opt_passes = [
    'mem2reg',
    'targetlibinfo',
    'no-aa',
    'basicaa',
    'memdep',
    'tbaa',
    'instcombine',
    'simplifycfg',
    'basiccg',
    'memdep',
    'scalarrepl-ssa',
    'sroa',
    'domtree',
    'early-cse',
    'simplify-libcalls',
    'lazy-value-info',
    'correlated-propagation',
    'simplifycfg',
    'instcombine',
    'reassociate',
    'domtree',
    'mem2reg',
    'scev-aa',
    'loops',
    'loop-simplify',
    'lcssa',
    'loop-rotate',
    'licm',
    'lcssa',
    'loop-unswitch',
    'instcombine',
    'scalar-evolution',
    'loop-simplify',
    'lcssa',
    'indvars',
    'loop-idiom',
    'loop-deletion',
    # 'loop-vectorize',
    'loop-unroll',
    
    'memdep',
    'gvn',
    'memdep',
    'sccp',
    'dse',
    'adce',
    'correlated-propagation',
    'jump-threading',
    'simplifycfg',
    'instcombine',
  ]

  def __init__(self, module_name, optimize = config.llvm_optimize,
               verify = config.llvm_verify):
    self.module = core.Module.new(module_name)
    self.engine_builder = ee.EngineBuilder.new(self.module)
    self.engine_builder.force_jit()
    opt_level = 3 if optimize else 0
    if optimize:
      self.engine_builder.opt(opt_level)
    else:
      self.engine_builder.opt(opt_level)
    self.exec_engine = self.engine_builder.create()
    tm = ee.TargetMachine.new(opt = opt_level)
    _, fpm = passes.build_pass_managers(tm, 
                                     opt = opt_level,
                                     loop_vectorize = (opt_level > 0), 
                                     mod = self.module)
    self.pass_manager = fpm 

    for p in self._verify_passes:
      self.pass_manager.add(p)
    if optimize:
      for p in (self._opt_passes + self._verify_passes):
        self.pass_manager.add(p)

  def run_passes(self, llvm_fn, n_iters = config.llvm_num_passes):
    for _ in xrange(n_iters):
      self.pass_manager.run(llvm_fn)

global_context = LLVM_Context("module")
