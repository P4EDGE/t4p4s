#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Copyright 2016 Eotvos Lorand University, Budapest, Hungary

import functools

#[ #pragma once

#[ #include <byteswap.h>
#[ #include <stdbool.h>
#[ #include "aliases.h"

#{ typedef enum parsed_field_attr_s {
#[     NOT_MODIFIED,
#[     MODIFIED,
#} } parsed_field_attr_t;


# hirefs = [(hdr, f'{f"{hdr.enclosing_control.name}_" if "enclosing_control" in hdr else ""}{hdr.urtype.name}') for hdr in hlir.header_instances if not hdr.urtype.is_metadata]
# hirefs = [(hdr, hdr.name) for hdr in hlir.header_instances if not hdr.urtype.is_metadata]
hirefs = [(hdr, hdr.name) for hdr in hlir.header_instances]
all_fields = [(hdr, hname, fld) for hdr, hname in hirefs for fld in hdr.urtype.fields]
parsed_fields = [(hdr, hname, fld) for hdr, hname, fld in all_fields if not fld.preparsed]
# parsed_fields = [(hdr, hname, fld) for hdr, hname, fld in all_fields if not fld.preparsed if fld.urtype.size <= 32]

for hdr, hname in hirefs:
    if hdr.urtype.node_type == 'Type_HeaderUnion':
        raise NotImplementedError("Header unions are not supported")

#{ typedef struct parsed_fields_s {
for hdr, hname, fld in parsed_fields:
    #[     uint32_t FLD(${hname},${fld._expression.name});
#[

for hdr, hname, fld in parsed_fields:
    #[     parsed_field_attr_t FLD_ATTR(${hname},${fld._expression.name});
#[
#} } parsed_fields_t;


#[ // Header instance infos
#[ // ---------------------

#[ #define HEADER_COUNT ${max(len(hirefs), 1)}
#[ #define FIELD_COUNT ${max(len(all_fields), 1)}

#[ extern const char* field_names[FIELD_COUNT];
#[ extern const char* header_instance_names[HEADER_COUNT];

# TODO maybe some more space needs to be added on for varlen headers?
nonmeta_hdrlens = "+".join([f'{hdr.urtype.byte_width}' for hdr, hname in hirefs])
#[ #define NONMETA_HDR_TOTAL_LENGTH ($nonmeta_hdrlens)


#[ #define FIXED_WIDTH_FIELD (-1)


#{ typedef enum header_instance_e {
for hdr, hname in hirefs:
    #[     HDR(${hdr.name}),
#} } header_instance_t;

#{ typedef enum field_instance_e {
for hdr, hname in hirefs:
    for fld in hdr.urtype.fields:
        #[   FLD(${hdr.name},${fld.name}),
#} } field_instance_t;

#[ // TODO documentation
#[ #define mod_top(n, bits) (((bits-(n%bits)) % bits))

#[ // Produces a 32 bit int that has n bits on at the top end.
#[ #define uint32_top_bits(n) (0xffffffff << mod_top(n, 32))


#{ struct hdr_info {
#[     int         idx;
#[     const char* name;
#[     int         byte_width;
#[     int         byte_offset;
#[     bool        is_metadata;
#[     int         var_width_field;
#} };

#{ struct fld_info {
#[     int               bit_width;
#[     int               bit_offset;
#[     int               byte_width;
#[     int               byte_offset;
#[     int               mask;
#[     bool              is_metadata;
#[     header_instance_t header_instance;
#} };



#{ static const struct hdr_info hdr_infos[HEADER_COUNT] = {
byte_offsets = ["0"]
for idx, (hdr, hname) in enumerate(hirefs):
    typ = hdr.urtype
    typ_bit_width = typ.bit_width if 'bit_width' in typ else 0
    typ_byte_width = typ.byte_width if 'byte_width' in typ else 0

    #[     // header ${hdr.name}
    #{     {
    #[         .idx = ${idx},
    #[         .name = "${hdr.name}",
    #[         .byte_width = ${typ_byte_width}, // ${typ_bit_width} bits, ${typ_bit_width/8.0} bytes
    #[         .byte_offset = ${"+".join(byte_offsets)},
    #[         .is_metadata = ${'true' if 'is_metadata' in typ and typ.is_metadata else 'false'},
    #[         .var_width_field = ${functools.reduce((lambda x, f: f.id if hasattr(f, 'is_vw') and f.is_vw else x), hdr.urtype.fields, 'FIXED_WIDTH_FIELD')},
    #}     },
    #[

    byte_offsets += [f'{typ_byte_width}']

if len(hlir.header_instances) == 0:
    #[ {}, // dummy
#} };


#{ static const struct fld_info fld_infos[FIELD_COUNT] = {
for hdr, hname in hirefs:
    for fld in hdr.urtype.fields:
        #[     // field ${hdr.name}.${fld.name}
        #{     {
        #[         .byte_width = ${hdr.urtype.byte_width},
        #[         .is_metadata = ${'true' if hdr.urtype.is_metadata else 'false'},
        #[         .bit_width = ${fld.urtype.size},
        #[         .bit_offset = ${fld.offset} % 8,
        #[         .byte_offset = ${fld.offset} / 8,
        #[         .mask = __bswap_constant_32(uint32_top_bits(${fld.urtype.size}) >> (${fld.offset}%8)),
        #[         .header_instance = HDR(${'all_metadatas' if hdr.urtype.is_metadata else hdr.name}),
        #}     },
        #[
#} };


#[ /////////////////////////////////////////////////////////////////////////////
#[ // HEADER TYPE AND FIELD TYPE INFORMATION

for enum in hlir.enums:
    #{ enum ${enum.c_name} {
    for m in enum.members:
        #[     ${m.c_name},
    #} };
#[

for error in hlir.errors:
    #{ enum ${error.c_name} {
    for m in error.members:
        #[     ${m.c_name},
    #} };
#[

#[ // HW optimization related infos
#[ // --------------------

#[ #define OFFLOAD_CHECKSUM ${'true' if []!=[x for x in hlir.sc_annotations if x.name=='offload'] else 'false'}


#[ // Parser state local vars
#[ // -----------------------

parser = hlir.parsers[0]

#{ typedef struct parser_state_s {
for loc in parser.parserLocals:
    if 'type_ref' in loc.type:
        if loc.urtype.node_type == 'Type_Extern':
            #[ ${loc.urtype.name}_t ${loc.name};
        else:
            #[ uint8_t ${loc.name}[${loc.urtype.byte_width}]; // type: ${loc.urtype.name}
    else:
        #[ uint8_t ${loc.name}[(${loc.type.size}+7)/8];
    #[ uint8_t ${loc.name}_var; // Width of the variable width field // type: ${loc.urtype.name}
if len(parser.parserLocals) == 0:
    #[     // no parser locals
#} } parser_state_t;
