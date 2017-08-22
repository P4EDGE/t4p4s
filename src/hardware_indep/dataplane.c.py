# Copyright 2016 Eotvos Lorand University, Budapest, Hungary
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from utils.hlir import parsed_field, fld_id
from utils.hlir16 import format_declaration_16, format_statement_16, format_expr_16
from utils.misc import addError, addWarning

#[ #include <stdlib.h>
#[ #include <string.h>
#[ #include <stdbool.h>
#[ #include "dpdk_lib.h"
#[ #include "actions.h"

#[ void mark_to_drop() {} // TODO

#[ uint16_t csum16_add(uint16_t num1, uint16_t num2) {
#[     if(num1 == 0) return num2;
#[     uint32_t tmp_num = num1 + num2;
#[     while(tmp_num > 0xffff)
#[         tmp_num = ((tmp_num & 0xffff0000) >> 16) + (tmp_num & 0xffff);
#[     return (uint16_t)tmp_num;
#[ }

#[ struct Checksum16 {
#[   uint16_t (*get) (uint8_t* data, int size, packet_descriptor_t* pd, lookup_table_t** tables);
#[ };
#[

#[ uint16_t Checksum16_get(uint8_t* data, int size, packet_descriptor_t* pd, lookup_table_t** tables) {
#[     uint32_t res = 0;
#[     res = csum16_add(res, calculate_csum16(data, size));
#[     res = (res == 0xffff) ? res : ((~res) & 0xffff);
#[     free(data);
#[     return res & ${hex((2 ** 16) - 1)};
#[ }

#[ void Checksum16_init(struct Checksum16* x) {
#[     x->get = &Checksum16_get;
#[ }

#[ extern void parse_packet(packet_descriptor_t* pd, lookup_table_t** tables);
#[ extern void increase_counter (int counterid, int index);

max_key_length = max([t.key_length_bytes for t in hlir16.tables])
#[ uint8_t reverse_buffer[${max_key_length}];

################################################################################

STDPARAMS = "packet_descriptor_t* pd, lookup_table_t** tables"

main = hlir16.declarations['Declaration_Instance'][0] # TODO what if there are more package instances?
package_name = main.type.baseType.path.name
pipeline_elements = main.arguments

#package_type = hlir16.declarations.get(package_name, 'Type_Package')

for pe in pipeline_elements:
    c = hlir16.declarations.get(pe.type.name, 'P4Control')
    if c is not None:
        #[ void control_${pe.type.name}(${STDPARAMS});
        for t in c.controlLocals['P4Table']:
            #[ void ${t.name}_apply(${STDPARAMS});

################################################################################

# TODO move this to HAL
def match_type_order_16(t):
    if t == 'EXACT':   return 0
    if t == 'LPM':     return 1
    if t == 'TERNARY': return 2
    else:              return 3

################################################################################
# Table key calculation

for table in hlir16.tables:
    # TODO find out why they are missing and fix it
    #      this happens if k is a PathExpression
    if any([k.get_attr('match_type') is None for k in table.key.keyElements]):
        continue

    #[ void table_${table.name}_key(packet_descriptor_t* pd, uint8_t* key) {
    sortedfields = sorted(table.key.keyElements, key=lambda k: match_type_order_16(k.match_type))
    #TODO variable length fields
    #TODO field masks
    for f in sortedfields:
        if f.get_attr('width') is None:
            # TODO find out why this is missing and fix it
            continue
        if f.width <= 32:
            #[ EXTRACT_INT32_BITS(pd, ${f.id}, *(uint32_t*)key)
            #[ key += sizeof(uint32_t);
        elif f.width > 32 and f.width % 8 == 0:
            byte_width = (f.width+7)/8
            #[ EXTRACT_BYTEBUF(pd, ${f.id}, key)
            #[ key += ${byte_width};
        else:
            add_error("table key calculation", "Unsupported field %s ignored." % f.id)
    if table.match_type == "LPM":
        #[ key -= ${table.key_length_bytes};
        #[ int c, d;
        #[ for(c = ${table.key_length_bytes-1}, d = 0; c >= 0; c--, d++) *(reverse_buffer+d) = *(key+c);
        #[ for(c = 0; c < ${table.key_length_bytes}; c++) *(key+c) = *(reverse_buffer+c);
    #[ }

################################################################################
# Table application

for table in hlir16.tables:
    lookupfun = {'LPM':'lpm_lookup', 'EXACT':'exact_lookup', 'TERNARY':'ternary_lookup'}
    #[ void ${table.name}_apply(${STDPARAMS})
    #[ {
    #[     debug("  :::: EXECUTING TABLE ${table.name}\n");
    #[     uint8_t* key[${table.key_length_bytes}];
    #[     table_${table.name}_key(pd, (uint8_t*)key);
    #[     uint8_t* value = ${lookupfun[table.match_type]}(tables[TABLE_${table.name}], (uint8_t*)key);
    #[     struct ${table.name}_action* res = (struct ${table.name}_action*)value;
    #[     int index; (void)index;

    # COUNTERS
    # TODO

    # ACTIONS
    #[     if(res == NULL) {
    #[       debug("    :: NO RESULT, NO DEFAULT ACTION.\n");
    #[     } else {
    #[       switch (res->action_id) {
    for action in table.actions:
        action_name = action.expression.method.path.name[:-2]
        if action_name == 'NoAction':
            continue
        #[         case action_${action_name}:
        #[           debug("    :: EXECUTING ACTION ${action_name}...\n");
        if action.action_object.parameters.parameters: # action.expression.arguments != []:
            #[           action_code_${action_name}(pd, tables, res->${action_name}_params);
        else:
            #[           action_code_${action_name}(pd, tables);
        #[           break;
    #[       }
    #[     }
    #[ }
    #[
    #[ struct ${table.name}_s {
    #[     void (*apply)(packet_descriptor_t* pd, lookup_table_t** tables);
    #[ };
    #[ struct ${table.name}_s ${table.name} = {.apply = &${table.name}_apply};

################################################################################

#[ void reset_headers(packet_descriptor_t* packet_desc) {
for h in hlir16.header_instances:
    if not h.type.is_metadata:
        #[ packet_desc->headers[${h.id}].pointer = NULL;
    else:
        #[ memset(packet_desc->headers[${h.id}].pointer, 0, header_info(${h.id}).bytewidth * sizeof(uint8_t));
#[ }

#[ void init_headers(packet_descriptor_t* packet_desc) {
for h in hlir16.header_instances:
    if not h.type.is_metadata:
        #[ packet_desc->headers[${h.id}] = (header_descriptor_t)
        #[ {
        #[     .type = ${h.id},
        #[     .length = header_info(${h.id}).bytewidth,
        #[     .pointer = NULL,
        #[     .var_width_field_bitwidth = 0
        #[ };
    else:
        #[ packet_desc->headers[${h.id}] = (header_descriptor_t)
        #[ {
        #[     .type = ${h.id},
        #[     .length = header_info(${h.id}).bytewidth,
        #[     .pointer = malloc(header_info(${h.id}).bytewidth * sizeof(uint8_t)),
        #[     .var_width_field_bitwidth = 0
        #[ };
#[ }

################################################################################

#TODO are these keyless tabls supported in p4-16?

def keyless_single_action_table(table):
    return table.key_length_bytes == 0 and len(table.actions) == 2 and table.actions[1].action_object.name.startswith('NoAction')

for table in hlir16.tables:
    if keyless_single_action_table(table):
        #[ extern void ${table.name}_setdefault(struct ${table.name}_action);

#[ void init_keyless_tables() {
for table in hlir16.tables:
    if keyless_single_action_table(table):
        action = table.actions[0].action_object
        #[ struct ${table.name}_action ${table.name}_a;
        #[ ${table.name}_a.action_id = action_${action.name};
        #[ ${table.name}_setdefault(${table.name}_a);
#[ }

################################################################################

#[ void init_dataplane(${STDPARAMS}) {
#[     init_headers(pd);
#[     reset_headers(pd);
#[     init_keyless_tables();
#[     pd->dropped=0;
#[ }

#[ void update_packet(packet_descriptor_t* pd) {
#[     uint32_t value32, res32;
#[     (void)value32, (void)res32;
for f in hlir.p4_fields.values():
    if parsed_field(hlir, f):
        if f.width <= 32:
#            #[ if(pd->headers[${hdr_prefix(f.instance.name)}].pointer != NULL) {
            #[ if(pd->fields.attr_${fld_id(f)} == MODIFIED) {
            #[     value32 = pd->fields.${fld_id(f)};
            #[     MODIFY_INT32_INT32_AUTO(pd, ${fld_id(f)}, value32)
            #[ }
#[ }

################################################################################
# Pipeline

for pe in pipeline_elements:
    c = hlir16.declarations.get(pe.type.name, 'P4Control')
    if c is not None:
        #[ void control_${pe.type.name}(${STDPARAMS})
        #[ {
        #[     uint32_t value32, res32;
        #[     (void)value32, (void)res32;
        for d in c.controlLocals:
            #[ ${format_declaration_16(d)}
        #[ ${format_statement_16(c.body)}
        #[ }

#[ void process_packet(${STDPARAMS})
#[ {
for pe in pipeline_elements:
    c = hlir16.declarations.get(pe.type.name, 'P4Control')
    if c is not None:
        #[ control_${pe.type.name}(pd, tables);
        if pe.type.name == 'egress':
            #[ update_packet(pd); // we need to update the packet prior to calculating the new checksum
#[ }

################################################################################

#[ void handle_packet(${STDPARAMS})
#[ {
#[     int value32;
#[     EXTRACT_INT32_BITS(pd, field_instance_standard_metadata_ingress_port, value32)
#[     debug("### HANDLING PACKET ARRIVING AT PORT %" PRIu32 "...\n", value32);
#[     reset_headers(pd);
#[     parse_packet(pd, tables);
#[     process_packet(pd, tables);
#[ }
