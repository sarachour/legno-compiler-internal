import itertools
import chip.abs as acirc
import chip.props as prop
import chip.conc_infer as conc_infer
from chip.config import Labels
import ops.aop as aop
import random
import math
import logging
import compiler.arco_pass.route as arco_route
from compiler.arco_pass.rules import get_rules
import compiler.arco_pass.to_abs_op as arcolib_aop
import compiler.arco_pass.to_abs_circ as arcolib_acirc
import compiler.arco_pass.make_fanouts as arcolib_mkfan
import compiler.arco_pass.util as arcolib_util
import compiler.arco_pass.util as arco_util

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('arco')


def bind_namespace(node,namespace,ids=[]):
    if node.id in ids:
        return

    node.set_namespace(namespace)
    if isinstance(node,acirc.AInput) and \
       not node.source is None:
        new_namespace = node.label
        rslv_node,_ = node.source
        bind_namespace(rslv_node,new_namespace,ids=ids + [node.id])

    else:
        for subn in node.subnodes():
            bind_namespace(subn,namespace,ids=ids + [node.id])

def compile_compute_fragments(board,prob,n_xforms):
    frag_node_map= {}
    frag_output_map= {}
    xform_map = {}
    rules = get_rules(board)
    for var,expr in prob.bindings():
        abs_expr = arcolib_aop.make_abstract(expr)
        frag_node_map[var] = []
        frag_output_map[var] = []
        xform_map[var] = []
        for dist_abs_expr in arcolib_aop.distribute_consts(abs_expr):
            for n_xforms,xform_abs_expr in dist_abs_expr.xform(rules,n_xforms):
                xform_map[var].append(xform_abs_expr)
                for node,output in arcolib_acirc.to_abs_circ(board,xform_abs_expr):
                    if isinstance(node,acirc.ABlockInst):
                        node.config.set_label(output,var,kind=Labels.OUTPUT)

                    if acirc.AbsCirc.feasible(board,[node]):
                        frag_node_map[var].append(node)
                        frag_output_map[var].append(output)


    return xform_map,frag_node_map,frag_output_map


def compile_sample_fragments_and_add_fanouts(board,frag_node_map, \
                                             frag_output_map):
    while True:
        frag_nodes = {}
        frag_outputs = {}
        print("-> sampling circuit")
        choices = arcolib_util.sample(frag_node_map)
        for variable,index in choices.items():
            frag_nodes[variable],_ = \
                                     frag_node_map[variable][index].copy()
            frag_outputs[variable] = frag_output_map[variable][index]

        # compute any references/stubs
        refs,stubs = arcolib_mkfan.count_var_refs(frag_nodes)

        subcs = {}
        skip_circuit = False
        # number of free fanouts for variable references
        free_fanouts = board.num_blocks("fanout") - \
                       acirc.AbsCirc.count_instances(board,\
                                    frag_nodes.values())["fanout"]

        for var_name,frag_node in frag_nodes.items():
            frag_output = frag_outputs[var_name]
            subcs[var_name] = []
            # make n copies of each variable for routing purposes.
            for sources,cnode in \
                arcolib_mkfan.copy_signal(board,frag_node,frag_output,
                                          refs[var_name], var_name, free_fanouts):

                other_frags = [v for k,v in frag_nodes.items() \
                               if k != var_name]

                if acirc.AbsCirc.feasible(board,[cnode]+other_frags):
                    subcs[var_name].append((sources,cnode))

            if len(subcs[var_name]) == 0:
                skip_circuit = True
                break

        if skip_circuit:
            print("-> invalid. skipping...")
            continue

        logger.info("--- Fan outs ---")
        for var,frags in subcs.items():
            logger.info("%s: %d" % (var,len(frags)))


        yield subcs

def compile_combine_fragments(subcircuit_optmap):
        variables = []
        subcirc_options = []
        subcirc_sources = {}
        subcirc_nodes = {}
        for variable,subcirc_opt in subcircuit_optmap.items():
            variables.append(variable)
            subcirc_options.append(range(0,len(subcirc_opt)))
            subcirc_sources[variable] = []
            subcirc_nodes[variable] = []
            for source,node in subcirc_opt:
                subcirc_sources[variable].append(source)
                subcirc_nodes[variable].append(node)


        for select_idx,selection in \
            enumerate(itertools.product(*subcirc_options)):
            source_map = {}
            node_map = {}
            for variable,index in zip(variables,selection):
                print(variable)
                source_map[variable] = subcirc_sources[variable][index]
                node_map[variable] = subcirc_nodes[variable][index]

            yield select_idx,source_map,node_map

def compile(board,prob,depth=3, \
            max_abs_circs=100, \
            max_fanout_circs=1, \
            max_conc_circs=1):

    xform_map,frag_node_map,frag_output_map = \
            compile_compute_fragments(board,prob,n_xforms=depth)

    logger.info("--- Fragments ---")
    for var,frags in frag_node_map.items():
        logger.info("====== %s ====" % (var))
        logger.info("# xforms: %d" %  len(xform_map[var]))
        logger.info("# unique-xforms: %d" %  len(set(map(lambda x: str(x),xform_map[var]))))
        for xform in xform_map[var]:
            print(xform)
        logger.info("# frags: %d" %  len(frags))
        if len(frags) == 0:
            raise Exception("cannot model variable <%s>" % var)

    try_abs = arco_util.TryObject('abs_circ',max_abs_circs,None)
    try_merge = arco_util.TryObject('merge_circ',max_fanout_circs,100)
    try_conc = arco_util.TryObject('conc_circ',max_conc_circs,None)

    for abs_idx, subcircuits_optmap in \
        try_abs.enumerate(compile_sample_fragments_and_add_fanouts(board, \
                                                                 frag_node_map,
                                                                   frag_output_map), \
                          do_succeed=False):


        try_merge.clear()
        try_conc.clear()
        print(">>> combine fragments <<<")
        for merge_idx,source_map,node_map in \
            try_merge.iterate(compile_combine_fragments(subcircuits_optmap),do_succeed=False):

            print("< TESTED UP TO HERE>")
            refs,stubs = arcolib_mkfan.count_var_refs(node_map)
            n_conc = 0;
            print(">>> compute matches from stubs to sources <<<")
            for stub_src_idx,mapping in \
                enumerate(arcolib_mkfan.match_stubs_to_sources(source_map,stubs)):

                if not try_conc.successes_left():
                    logger.info("-> found %d/%d conc circuits" % \
                                (n_conc,max_conc_circs))
                    break
                print(">>> connect stubs to sources <<<")
                arcolib_mkfan.connect_stubs_to_sources(board,
                                                       node_map, \
                                                       mapping)

                print(">>> bind namespaces <<<")
                for var,node in node_map.items():
                    bind_namespace(node,var)

                print(">>> route <<<")
                for route_index,conc_circ in try_conc.enumerate(arco_route.route(board,
                                                                                 prob,
                                                                                 node_map,
                                                                                 max_failures=100,
                                                                                 max_resolutions=100)):

                    indices = [abs_idx,merge_idx,stub_src_idx,route_index]
                    try_merge.succeed()
                    try_abs.succeed()
                    yield indices,conc_circ


