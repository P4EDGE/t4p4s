# SPDX-License-Identifier: Apache-2.0
# Copyright 2016 Eotvos Lorand University, Budapest, Hungary

#[ #include <unistd.h>

#[ #include "dpdk_lib.h"
#[ #include "actions.h"
#[ #include "tables.h"

#[ extern void table_setdefault_promote  (int tableid, uint8_t* value);
#[ extern void exact_add_promote  (int tableid, uint8_t* key, uint8_t* value, bool should_print);
#[ extern void lpm_add_promote    (int tableid, uint8_t* key, uint8_t depth, uint8_t* value, bool should_print);
#[ extern void ternary_add_promote(int tableid, uint8_t* key, uint8_t* mask, uint8_t* value, bool should_print);


for table in hlir.tables:
    #[ extern void table_${table.name}_key(packet_descriptor_t* pd, uint8_t* key); // defined in dataplane.c


max_bytes = max([0] + [t.key_length_bytes for t in hlir.tables])
#[ uint8_t reverse_buffer[$max_bytes];

# Variable width fields are not supported
def get_key_byte_width(k):
    # for special functions like isValid
    if 'header' not in k:
        return 0
    
    if k.header.urtype('is_vw', False):
        return 0

    if 'size' in k:
        return (k.size+7)//8

    # reaching this point, k can only come from metadata
    return (k.header.type.size+7)//8


keyed_table_names = ", ".join([f'"T4LIT({table.name},table)"' for table in hlir.tables])


for table in hlir.tables:
    import inspect; import pprint; pprint.PrettyPrinter(indent=4,width=999,compact=True).pprint([f"controlplane.c.py@{inspect.getframeinfo(inspect.currentframe()).lineno}", table])
    if 'matchType' not in table:
        breakpoint()
    #[ // note: ${table.name}, ${table.matchType}, ${table.key_length_bytes}
    #{ void ${table.name}_add(
    for k in table.key.keyElements:
        # TODO should properly handle specials (isValid etc.)
        if 'header' not in k:
            continue

        byte_width = get_key_byte_width(k)
        #[ uint8_t field_${k.header.name}_${k.field_name}[$byte_width],
        
        # TODO have keys' and tables' matchType the same case (currently: LPM vs lpm)
        if k.matchType == "ternary":
            #[ uint8_t ${k.field_name}_mask[$byte_width],
        if k.matchType == "lpm":
            #[ uint8_t field_${k.header.name}_${k.field_name}_prefix_length,

    #}     struct ${table.name}_action action, bool has_fields)
    #{ {

    #[     uint8_t key[${table.key_length_bytes}];

    byte_idx = 0
    import inspect; import pprint; pprint.PrettyPrinter(indent=4,width=999,compact=True).pprint([f"controlplane.c.py@{inspect.getframeinfo(inspect.currentframe()).lineno}", table.key.keyElements.map('matchType.path.name')])
    for k in sorted((k for k in table.key.keyElements), key = lambda k: k.match_order):
        # TODO should properly handle specials (isValid etc.)
        if 'header' not in k:
            continue

        byte_width = get_key_byte_width(k)
        #[ memcpy(key+$byte_idx, field_${k.header.name}_${k.field_name}, $byte_width);
        byte_idx += byte_width

    if table.matchType == "lpm":
        #[ uint8_t prefix_length = 0;
        for k in table.key.keyElements:
            # TODO should properly handle specials (isValid etc.)
            if 'header' not in k:
                continue

            if k.matchType == "exact":
                #[ prefix_length += ${get_key_byte_width(k)};
            if k.matchType == "lpm":
                #[ prefix_length += field_${k.header.name}_${k.field_name}_prefix_length;
        #[ int c, d;
        #[ for(c = ${byte_idx-1}, d = 0; c >= 0; c--, d++) *(reverse_buffer+d) = *(key+c);
        #[ for(c = 0; c < ${byte_idx}; c++) *(key+c) = *(reverse_buffer+c);
        #[ lpm_add_promote(TABLE_${table.name}, (uint8_t*)key, prefix_length, (uint8_t*)&action, has_fields);

    if table.matchType == "exact":
        #[ exact_add_promote(TABLE_${table.name}, (uint8_t*)key, (uint8_t*)&action, has_fields);

    #} }

for table in hlir.tables:
    #{ void ${table.name}_add_table_entry(struct p4_ctrl_msg* ctrl_m) {
    for i, k in enumerate(table.key.keyElements):
        # TODO should properly handle specials (isValid etc.)
        if 'header' not in k:
            continue

        if k.matchType == "exact":
            #[ uint8_t* field_${k.header.name}_${k.field_name} = (uint8_t*)(((struct p4_field_match_exact*)ctrl_m->field_matches[${i}])->bitmap);
        if k.matchType == "lpm":
            #[ uint8_t* field_${k.header.name}_${k.field_name} = (uint8_t*)(((struct p4_field_match_lpm*)ctrl_m->field_matches[${i}])->bitmap);
            #[ uint16_t field_${k.header.name}_${k.field_name}_prefix_length = ((struct p4_field_match_lpm*)ctrl_m->field_matches[${i}])->prefix_length;
        if k.matchType == "ternary":
            # TODO are these right?
            #[ uint8_t* field_${k.header.name}_${k.field_name} = (uint8_t*)(((struct p4_field_match_lpm*)ctrl_m->field_matches[${i}])->bitmap);
            #[ uint16_t field_${k.header.name}_${k.field_name}_prefix_length = ((struct p4_field_match_lpm*)ctrl_m->field_matches[${i}])->prefix_length;

    for action in table.actions:
        #{ if(strcmp("${action.action_object.name}", ctrl_m->action_name)==0) {
        #[     struct ${table.name}_action action;
        #[     action.action_id = action_${action.action_object.name};
        for j, p in enumerate(action.action_object.parameters.parameters):
            #[ uint8_t* bitmap_${p.name} = (uint8_t*)((struct p4_action_parameter*)ctrl_m->action_params[$j])->bitmap;
            #[ memcpy(action.${action.action_object.name}_params.${p.name}, bitmap_${p.name}, ${(p.urtype.size+7)//8});

        params = []
        for i, k in enumerate(table.key.keyElements):
            if 'header' not in k:
                continue

            params.append(f'field_{k.header.name}_{k.field_name}')
            if k.matchType == "lpm":
                params.append(f"field_{k.header.name}_{k.field_name}_prefix_length")
            if k.matchType == "ternary":
                params.append("0 /* TODO ternary dstPort_mask */")

        has_fields = "false" if len(action.action_object.parameters.parameters) == 0 else "true"
        joined_params = ', '.join(params + ["action", has_fields])
        #[ ${table.name}_add($joined_params);

        for j, p in enumerate(action.action_object.parameters.parameters):
            size = p.urtype.size
            #[ dbg_print(bitmap_${p.name}, $size, "       : $$[field]{p.name}");

        #} } else

    valid_actions = ", ".join([f'" T4LIT({a.action_object.name},action) "' for a in table.actions])
    #[     debug(" $$[warning]{}{!!!! Table add entry} on table $$[table]{table.name}: action name $$[warning]{}{mismatch}: $$[action]{}{%s}, expected one of ($valid_actions).\n", ctrl_m->action_name);
    #} }
    #[

for table in hlir.tables:
    #{ void ${table.name}_set_default_table_action(struct p4_ctrl_msg* ctrl_m) {
    for action in table.actions:
        #{ if(strcmp("${action.action_object.name}", ctrl_m->action_name)==0) {
        #[     struct ${table.name}_action action;
        #[     action.action_id = action_${action.action_object.name};
        for j, p in enumerate(action.action_object.parameters.parameters):
            #[ uint8_t* ${p.name} = (uint8_t*)((struct p4_action_parameter*)ctrl_m->action_params[$j])->bitmap;
            #[ memcpy(action.${action.action_object.name}_params.${p.name}, ${p.name}, ${(p.urtype.size+7)//8});
        #[     debug(" " T4LIT(ctl>,incoming) " " T4LIT(Set default action,action) " for $$[table]{table.name}: $$[action]{action.action_object.name}\n");
        #[     table_setdefault_promote(TABLE_${table.name}, (uint8_t*)&action);
        #} } else

    valid_actions = ", ".join(["\" T4LIT(f{a.action_object.name},action) \"" for a in table.actions])
    #[ debug(" $$[warning]{}{!!!! Table setdefault} on table $$[table]{table.name}: action name $$[warning]{}{mismatch} ($$[action]{}{%s}), expected one of ($valid_actions).\n", ctrl_m->action_name);
    #} }
    #[


#{ void ctrl_add_table_entry(struct p4_ctrl_msg* ctrl_m) {
for table in hlir.tables:
    if table.key_length_bits == 0:
        continue

    #{ if (strcmp("${table.name}", ctrl_m->table_name) == 0) {
    #[     ${table.name}_add_table_entry(ctrl_m);
    #[     return;
    #} }
#[     debug(" $$[warning]{}{!!!! Table add entry}: table name $$[warning]{}{mismatch} ($$[table]{}{%s}), expected one of ($keyed_table_names).\n", ctrl_m->table_name);
#} }


#[ extern char* action_names[];

#{ void ctrl_setdefault(struct p4_ctrl_msg* ctrl_m) {
for table in hlir.tables:
    #{ if (strcmp("${table.name}", ctrl_m->table_name) == 0) {
    #[     ${table.name}_set_default_table_action(ctrl_m);
    #[     return;
    #} }

#[     debug(" $$[warning]{}{!!!! Table setdefault}: table name $$[warning]{}{mismatch} ($$[table]{}{%s}), expected one of ($keyed_table_names).\n", ctrl_m->table_name);
#} }


#[ extern struct socket_state state[NB_SOCKETS];

#[ extern volatile int ctrl_is_initialized;

#{ void ctrl_initialized() {
#[     debug("   " T4LIT(::,incoming) " Control plane init " T4LIT(done,success) "\n");
#[     ctrl_is_initialized = 1;
#} }


#{ void recv_from_controller(struct p4_ctrl_msg* ctrl_m) {
#{     if (ctrl_m->type == P4T_ADD_TABLE_ENTRY) {
#[         ctrl_add_table_entry(ctrl_m);
#[     } else if (ctrl_m->type == P4T_SET_DEFAULT_ACTION) {
#[         ctrl_setdefault(ctrl_m);
#[     } else if (ctrl_m->type == P4T_CTRL_INITIALIZED) {
#[         ctrl_initialized();
#}     }
#} }


#[ ctrl_plane_backend bg;
#[ void init_control_plane()
#[ {
#[     bg = create_backend(3, 1000, "localhost", 11111, recv_from_controller);
#[     launch_backend(bg);
#[ 
#[     #ifdef T4P4S_DEBUG
#[     for (int i = 0; i < NB_TABLES; i++) {
#[         lookup_table_t t = table_config[i];
#[         if (state[0].tables[t.id][0]->init_entry_count > 0)
#[             debug("    " T4LIT(:,incoming) " Table " T4LIT(%s,table) " got " T4LIT(%d) " entries from the control plane\n", state[0].tables[t.id][0]->name, state[0].tables[t.id][0]->init_entry_count);
#[         }
#[     #endif
#[ }
